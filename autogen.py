import glob
import importlib.util
import json
import platform
import random
import re
import shutil
import string
import sys
import time
from enum import Enum
import os
from typing import List, Union, Tuple, Dict, TypedDict, Any

from autogen_logging import set_loglevel, log, log_error, log_info, log_failure, log_success, LOGLEVEL, is_debug

CRITICAL = LOGLEVEL.CRITICAL
INFO_QUIET = LOGLEVEL.INFO_QUIET
INFO = LOGLEVEL.INFO
DEBUG = LOGLEVEL.DEBUG

import requests


# type "alias"
class FileActionVariable(TypedDict):
    method: str
    args: List[Any]


class FileConfig:
    @staticmethod
    def from_json(data):
        # variables are simple enough as is.
        # we just need to turn the actions into objects
        action_objs = []
        for action in data["actions"]:
            line_str = action.get("match_lines")
            lines = []
            line_group_ends = []

            if line_str:
                segments = re.split(r", *", line_str)
                for seg in segments:
                    matched = re.match(r"(\d+)-?(\d+)?", seg)
                    # if group 1 and 2 are present, we have a "-".
                    # otherwise, we have a single number
                    if matched.group(2):
                        lines.extend(range(int(matched.group(1)), int(matched.group(2)) + 1))
                        line_group_ends.append(int(matched.group(2)))
                    else:
                        lines.append(int(matched.group(1)))
                        line_group_ends.append(int(matched.group(1)))

            # cast to set to remove duplicates then sort
            lines = tuple(sorted(list(set(lines))))
            line_group_ends = tuple(line_group_ends)

            action_objs.append(FileAction(
                action.get("source_file"),
                action.get("source_text"),
                action.get("source_code"),
                action.get("target_file"),
                FileAction.TargetHost[str(action.get("target_host", "IMAGE")).upper()],
                FileAction.ChangeType[str(action.get("action_type")).upper()],
                lines,
                line_group_ends,
                action.get("match_regex")
            ))

        return FileConfig(data["variables"], action_objs)

    def __init__(self, variables=None, actions=()):
        self.variables: Dict[str, Union[str, int, FileActionVariable]] = variables if variables else {}
        self.calculated_variables: Dict[str, Any] = {}

        self.actions: List[FileAction] = list(actions)

    def resolve_variables(self, constants: Dict[str, Any]):
        calced = {}
        for k in self.variables.keys():
            calced[k] = FileAction.resolve_variable(k, self.variables, constants)

        return calced

    def get_present_files(self):
        # gets files which have been placed by this action set
        present_files = []
        for action in self.actions:
            if action.action_type == FileAction.ChangeType.COPY:
                path = action.get_image_path()
                if path:
                    present_files.append(path)

        return present_files

    def get_required_files(self):
        required_files = []
        for action in self.actions:
            dependent_actions = [
                FileAction.ChangeType.APPEND, FileAction.ChangeType.REPLACE
            ]
            if action.action_type in dependent_actions:
                path = action.get_image_path()
                if path:
                    required_files.append(path)

        return required_files

    def commit(self, constants: Dict[str, Any], source_dir: str, staging_dir: str, only_copy: bool = False):
        self.calculated_variables = self.resolve_variables(constants)

        for action in self.actions:
            if action.action_type == FileAction.ChangeType.COPY or not only_copy:
                action.commit(
                    self.calculated_variables, constants, source_dir, staging_dir
                )


class FileAction:
    @staticmethod
    def random_alnum(length):
        return "".join(
            random.choice((*string.digits, *string.ascii_lowercase, *string.ascii_uppercase)) for _ in range(length)
        )

    @staticmethod
    def resolve_variable(s: str, variables: Dict[str, FileActionVariable], constants: Dict[str, Any]):
        # match for if it's of the X["y"] form
        match = re.match('(\w+)\["(\w+)"]', s)
        if match:
            base = match.group(1)
            index = match.group(2)

            if base in constants:
                return constants.get(base).get(index)

            if base in variables:
                return variables.get(base).get(index)

        if s in constants:
            return constants.get(s)

        v = variables.get(s)
        if isinstance(v, dict):
            # it's a "call function" kinda day
            method = v.get("method")
            args = v.get("args")
            if method in FileAction.valid_functions:
                if args:
                    # call the method, unpack args using *, hope it works
                    return getattr(FileAction, v.get("method"))(*args)
                else:
                    raise ValueError("args not supplied (trying to call variable method {})".format(method))
            else:
                raise ValueError("method not valid (tried {}, possible methods are ({}))".format(
                    method, ", ".join(t for t in FileAction.valid_functions)
                ))
        else:
            return variables.get(s)

    valid_functions = [
        "random_alnum"
    ]

    class TargetHost(Enum):
        NONE = 0
        HOST = 1
        IMAGE = 2

    class ChangeType(Enum):
        NONE = 0
        COPY = 1
        REPLACE = 2
        APPEND = 3
        DELETE = 4
        COPYBIN = 5

    def __init__(self, source_file="", source_text="", source_code="", target_file="", target_host=TargetHost.NONE,
                 action_type=ChangeType.NONE, match_lines=(), line_group_ends=(), match_regex=""):
        self.source_file: str = source_file
        self.source_text: str = source_text
        self.source_code: str = source_code
        self.target_file: str = target_file
        self.target_host: FileAction.TargetHost = target_host
        self.action_type: FileAction.ChangeType = action_type
        self.match_lines: Tuple[int] = match_lines
        self.line_group_ends: Tuple[int] = line_group_ends
        self.match_regex: str = match_regex

        # if self.match_lines:
        #     log_info(LOGLEVEL.DEBUG, "{:60} | lines: {:24} | group ends: {}".format(
        #         "{} => {}:{}".format(
        #             self.source_file if self.source_file else (
        #                 self.source_text if self.source_text else self.source_code
        #             ),
        #             "img" if self.target_host.value == FileAction.TargetHost.IMAGE.value else "host",
        #             self.target_file
        #         ), str(self.match_lines), str(self.line_group_ends)
        #     ))

    def __str__(self):
        return "source_file: {s.source_file}\n" \
               "source_text: {s.source_text}\n" \
               "source_code: {s.source_code}\n" \
               "target_file: {s.target_file}\n" \
               "target_file: {s.target_host}\n" \
               "action_type: {s.action_type}\n" \
               "match_lines: {s.match_lines}\n" \
               "match_regex: {s.match_regex}\n".format(s=self)

    def get_image_path(self):
        # returns the path on the image of the file. used for speculation

        if self.action_type == FileAction.ChangeType.NONE:
            raise ValueError("action_type is not set to a usable enum value (currently .NONE)")

        if self.target_host == FileAction.TargetHost.HOST:
            return None
        else:  # "IMAGE" is an implicit parameter (so "NONE" means "IMAGE")
            # it may be the case that we have a linux pathname ("/root/scrimblo/...".)
            # we need to remove the "/" at the start
            original_path = self.target_file
            if original_path.startswith("/"):
                original_path = original_path.lstrip("/")

            return os.path.join("/" + original_path)

    def commit(self, variables: Dict[str, FileActionVariable], constants: Dict[str, Any], source_dir: str,
               staging_dir: str, speculating_changes: bool = False):
        # logic to act on these parameters here
        # in the staging directory, there will be a folder called "image_files" which emulates linux paths
        # assuming the contents of "image_files" is the root.
        # we can't edit any configuration files on docker so the base should always be COPY actions
        # constants are the stuff in "$$" like FLAG or BASE.

        # we also have DELETE which is the only directive that doesn't need source information - or anything, really,
        # except target_file and target_host.

        # if COPYBIN, we don't ever get file content and just copy it directly

        # step 1: get the content. if source_file is present, load that, otherwise copy from source_text
        source_content = ""
        if self.action_type != FileAction.ChangeType.COPYBIN:
            if self.source_file:
                with open(os.path.join(source_dir, self.source_file), "r", encoding="utf-8") as f:
                    source_content = f.read()
            elif self.source_text is not None:
                source_content = self.source_text
            elif self.source_code:
                sourcepath = os.path.join(source_dir, self.source_code)
                spec = importlib.util.spec_from_file_location("autogen_dynamic_import", sourcepath)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                source_content = module.generate()
            elif self.action_type == FileAction.ChangeType.DELETE:
                source_content = ""  # we'll delete it later
            else:
                raise ValueError("No source information (source_file or source_text) set")

        # step 2: set then verify the target and action type.
        # raise an error if we try to do anything except COPY into a nonexistent file.
        # if the action is NONE, error now
        if self.action_type == FileAction.ChangeType.NONE:
            raise ValueError("action_type is not set to a usable enum value (currently .NONE)")

        if self.target_host == FileAction.TargetHost.HOST:
            if self.action_type == FileAction.ChangeType.DELETE:
                raise ValueError("DELETE is not a valid action type on HOST targets (tried to DELETE {})".format(
                    self.target_file
                ))

            target_path = os.path.join(staging_dir, self.target_file)
        else:  # "IMAGE" is an implicit parameter (so "NONE" means "IMAGE")
            # it may be the case that we have a linux pathname ("/root/scrimblo/...".)
            # we need to remove the "/" at the start
            original_path = self.target_file
            if original_path.startswith("/"):
                original_path = original_path.lstrip("/")

            target_set = "image_delete" if self.action_type == FileAction.ChangeType.DELETE else "image_files"
            target_path = os.path.join(staging_dir, target_set, original_path)

        # consider security around file targets and sources, prevent path traversal

        # check if file does not exist, if it doesn't, raise an exception unless the action is COPY
        # if the file happens to be a directory, it's always an error.
        if os.path.isdir(target_path):
            raise ValueError("Tried to use target path {}, which exists already as a directory. "
                             "Only file paths are valid.".format(target_path))

        if not os.path.isfile(target_path):
            # we covered the isdir branch already so this is a binary between exists and not exists
            if self.action_type != FileAction.ChangeType.COPY and self.action_type != FileAction.ChangeType.COPYBIN and self.action_type != FileAction.ChangeType.DELETE:
                raise ValueError("Trying to do action_type {} to a nonexistent file ({}). "
                                 "Only COPY is allowed on nonexistent files.".format(str(self.action_type),
                                                                                     target_path))

        # now we should have ensured that our action type is valid and we have a working path.
        # step 3: preprocess the source_content with variables and constants
        # $$variablename$$
        processed_source_content = re.sub(
            r"(\$\$(.*?)\$\$)",
            lambda s: str(FileAction.resolve_variable(s.group(2), variables, constants)),
            source_content
        )

        # step 4: actually do the damn thing.
        # COPY can now be done with no further processing while APPEND and REPLACE need a litle more.
        # APPEND and REPLACE operate under the hood by loading in the entire file, making the edits
        # and saving the whole file again.
        if self.action_type == FileAction.ChangeType.COPY:
            final_content = processed_source_content
        elif self.action_type == FileAction.ChangeType.DELETE:
            final_content = " -- THIS FILE SHOULD BE DELETED BY AUTOGEN -- "
        elif self.action_type in (FileAction.ChangeType.APPEND, FileAction.ChangeType.REPLACE):
            # step 4.1: load in the target file
            with open(target_path, "r", encoding="utf-8") as f:
                target_file_content = f.read()

            # step 4.2: get the lines / regex for replace. there's no reason to disallow both, either
            final_content = ""
            if self.match_lines:
                for lineno, line in enumerate(target_file_content.splitlines()):
                    # 1-indexed lines
                    if lineno in self.match_lines:
                        # we always add the source content. it's just a matter of if we also add the original line
                        if self.action_type == FileAction.ChangeType.APPEND:
                            final_content += line + "\n"

                        # REPLACE behaves slightly differently -
                        # groups of match_lines will only trigger a replace on the final line.
                        if self.action_type != FileAction.ChangeType.REPLACE or lineno in self.line_group_ends:
                            final_content += processed_source_content + (
                                "" if processed_source_content.endswith("\n") else "\n"
                            )
                    else:
                        final_content += line + "\n"

            if self.match_regex:
                # simple re.sub
                if self.action_type == FileAction.ChangeType.REPLACE:
                    final_content = re.sub(
                        self.match_regex, processed_source_content, target_file_content
                    )
                else:
                    final_content = re.sub(
                        self.match_regex, "\\g<0>\n" + processed_source_content, target_file_content
                    )
        elif self.action_type == FileAction.ChangeType.COPYBIN:
            copy_full_path(os.path.join(source_dir, self.source_file), target_path)
            return
        else:
            raise ValueError("Unknown action_type (.{})".format(str(self.action_type)))

        # it's time
        save_full_path(final_content, target_path)


class Template:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.file_path = os.path.join(path, "files")  # for convenience

        self.desc = ""

        # preprocess actions and things like that here
        self.config: Union[dict, None] = None
        self.files: Union[FileConfig, None] = None

    def __eq__(self, other):
        if isinstance(other, Template):
            return self.name == other.name
        else:
            return False

    def load_information(self):
        # load info from the config files now
        # subclasses will perform further processing on this for specific things they need
        with open(os.path.join(self.path, "config.json"), "r", encoding="utf-8") as config_file:
            self.config = json.load(config_file)
            self.name = self.config["name"]
            self.desc = self.config["desc"]

        with open(os.path.join(self.path, "files.json"), "r", encoding="utf-8") as files_file:
            file_json = json.load(files_file)
            self.files = FileConfig.from_json(file_json)

    def is_compatible(self, staging_location):
        # base template is never compatible
        raise TypeError("Template is abstract and should not be added to any staging location. Use a subclass"
                        " (BaseTemplate, SiteTemplate, VulnTemplate).")


class BaseTemplate(Template):
    def __init__(self, name, path):
        super().__init__(name, path)

        self.base_type = None

        self.load_information()

    def load_information(self):
        super().load_information()

        self.base_type = self.config["type"].upper()

    def is_compatible(self, staging_location):
        # bases are always compatible unless a base of the same type is already present
        return not staging_location.base_type_present(self.base_type)


class SiteTemplate(Template):
    def __init__(self, name, path):
        super().__init__(name, path)

        self.required_bases = []
        self.compatible_bases = []

        self.load_information()

    def load_information(self):
        super().load_information()

        self.required_bases = self.config["required_bases"]
        self.compatible_bases = self.config["compatible_bases"]

    def is_compatible(self, staging_location):
        # sites are compatible if:
        # - all bases in required_bases are present
        # - the web base present is in compatible_bases
        return all(
            staging_location.base_type_present(req_base) for req_base in self.required_bases
        ) and any(
            staging_location.base_present_fuzzy(compat_base) for compat_base in self.compatible_bases
        )


class VulnTemplate(Template):
    def __init__(self, name, path):
        super().__init__(name, path)

        self.difficulty = 0
        self.briefing = ""
        self.compatible_sites = None
        self.compatible_bases = None
        self.tags = []

        self.load_information()

    def load_information(self):
        super().load_information()

        self.difficulty = self.config["difficulty"]
        self.briefing = self.config["briefing"]
        self.compatible_sites = self.config["compatible_sites"]
        self.compatible_bases = self.config["compatible_bases"]
        self.tags = self.config["tags"]

    def is_compatible(self, staging_location):
        # vulns are compatible if:
        # - the web base is in compatible_bases
        # - the site is in compatible_sites
        return any(
            staging_location.base_present_fuzzy(compat_base) for compat_base in self.compatible_bases
        ) and any(
            staging_location.site_present_fuzzy(compat_site) for compat_site in self.compatible_sites
        )


class StagingLocation:
    def __init__(self, root_path):
        self.root_path = root_path
        self.bases: List[BaseTemplate] = []  # bases are given a path based on their name, inside root_path.
        self.site: Union[
            SiteTemplate, None] = None  # sites are linked to a base and given a path based on their name, inside root_path.

        # vulns are linked to sites. our current plan is to only apply vulns to the site and web base configs,
        # not "modules" like an SQL server.
        self.vulns: List[VulnTemplate] = []

    def add(self, template: Template):
        if template.is_compatible(self):
            # if it's compatible, add it to the list ready to be staged
            if isinstance(template, BaseTemplate):
                self.bases.append(template)
            elif isinstance(template, SiteTemplate):
                self.site = template
            elif isinstance(template, VulnTemplate):
                self.vulns.append(template)
        else:
            raise ValueError("Template was not compatible: {}".format(str(template)))

    def preload_required_files(self):
        # we need to check and see if we need any files from the containers. if we do, we need to start them
        # and copy them into the staging area, before starting with the template changes.
        # each template can tell us what files it needs to exist beforehand
        base_req_files = {}
        for base in self.bases:
            required_files = base.files.get_required_files()
            present_files = base.files.get_present_files()

            if base.base_type.lower() == "web":
                for template in [self.site, *self.vulns]:
                    added_reqs = template.files.get_required_files()
                    added_present = template.files.get_present_files()

                    present_files.extend(f for f in added_present if f not in present_files)
                    required_files.extend(f for f in added_reqs if f not in required_files and f not in present_files)

            base_req_files[base.base_type] = [required_files, base]

        for base in base_req_files:
            required = base_req_files[base][0]
            base_obj = base_req_files[base][1]

            if required:
                log_info(LOGLEVEL.DEBUG, "preloading files for".format(base_obj.name))
                log(LOGLEVEL.DEBUG, " - copying Dockerfile")
                # copy the Dockerfile into the staging directory
                constants = {
                    "FLAG": "flag{test_flag_for_speculation}",

                    "BASE": {

                    }
                }

                files_path = os.path.join(self.root_path, "base_spec")
                os.makedirs(os.path.join(files_path, "image_files"), exist_ok=True)
                base_obj.files.commit(constants, base_obj.file_path, files_path, only_copy=True)

                # create a docker image with the files in it, copy the files off, delete the image

                # cleanup just in case
                silent_os_system("docker rm -f container_spec".format())
                silent_os_system("docker image rm -f img_spec".format())

                saved_path = os.getcwd()
                os.chdir(files_path)

                # build
                log(LOGLEVEL.DEBUG, "- building")
                cmd = "docker build -t img_spec ."
                silent_os_system(cmd)

                # create
                cmd = "docker create --name container_spec img_spec"
                silent_os_system(cmd)

                base_folder_name = "base_{}".format(base)
                for f in required:
                    image_path = f
                    local_path = os.path.join(saved_path, "staging", base_folder_name, "image_files", f.lstrip("/"))

                    log(LOGLEVEL.DEBUG, "- preloading {} => {}".format(image_path, local_path))
                    os.makedirs(os.path.dirname(local_path))
                    silent_os_system(
                        "docker cp container_spec:{} {}".format(f, local_path)
                    )

                # cleanup
                silent_os_system("docker rm -f container_spec".format())
                silent_os_system("docker image rm -f img_spec".format())

                os.chdir(saved_path)

    def clean_staging(self):
        # clear staging dir then delete docker stuff

        # delete everything inside our staging directory
        erase_from_directory(self.root_path)

    def clean_setup(self):
        log_info(LOGLEVEL.INFO, "cleaning up old container data")
        for base in self.bases:
            silent_os_system("docker rm -f container_{}".format(base.base_type.lower()))
            silent_os_system("docker image rm -f img_{}".format(base.base_type.lower()))

        log_info(LOGLEVEL.DEBUG, "deleting docker network")
        silent_os_system("docker network rm autogen-net")

    def stage(self, flag):
        # starting from the bases, then the site, then the vulns, copy the things in order.
        # for the bases, we need to copy each into a different staging directory
        # then the site will work within the web base's staging directory
        # and the vulns will be added there too
        #
        # the commit() function of FileAction should do most of the lifting for us
        #
        # each base will have a separate folder in staging but we only care about our WEB base's
        # folder after we begin copying in sites and vulns
        #
        # the image_files/ subdirectory in the staging location refers to files which will be copied to
        # the docker container after it's created (but not yet started).
        # files outside this directory will be used in the cwd when it comes time to spawn the docker.
        # e.g. dockerfiles

        self.clean_staging()

        # preload required files
        for base in self.bases:
            base_folder_name = "base_{}".format(str(base.base_type))

            # make the directory for the base and "image_files" within that
            os.makedirs(os.path.join(self.root_path, base_folder_name, "image_files"), exist_ok=True)
            os.makedirs(os.path.join(self.root_path, base_folder_name, "image_delete"), exist_ok=True)

        self.preload_required_files()

        constants = {
            "FLAG": flag,

            "BASE": {

            }
        }

        for base in self.bases:
            base_folder_name = "base_{}".format(str(base.base_type))

            # commit all file changes
            files_path = os.path.join(self.root_path, base_folder_name)
            base.files.commit(constants, base.file_path, files_path)

            # save variables
            constants["SAVEDVARS_{}".format(base.base_type.upper())] = base.files.calculated_variables
            constants["BASE"][base.base_type.upper()] = "container_{}".format(base.base_type.lower())
            log(LOGLEVEL.DEBUG, "constants:", constants)

        # from here, we only care about the WEB base
        base_path = os.path.join(self.root_path, "base_WEB")

        if self.site:
            self.site.files.commit(constants, self.site.file_path, base_path)

        # now do vulns
        for vuln in self.vulns:
            vuln.files.commit(constants, vuln.file_path, base_path)

        # we are now done!
        log_success(LOGLEVEL.INFO, "staging complete")

    def setup(self, port):
        # we assume our staging directory is now fully ready.
        # from here, we need to:
        # 1) create docker images for each base (using the Dockerfile that should be in the base's dir)
        # 2) copy the files from the base's image_files/ dir into the docker container, using the
        #    path of the file after image_files/ as an absolute linux path
        #    (image_files/root/scrimblo becomes /root/scrimblo)
        # 3) network the containers together if necessary
        # 4) start all of them!
        saved_path = os.getcwd()

        # first make the docker network which we'll put everything else on
        # this means we can later refer to other containers just by their name and docker just works !!!
        self.clean_setup()

        log_info(LOGLEVEL.INFO, "setting up docker network")
        silent_os_system("docker network create --driver bridge autogen-net")

        log_info(LOGLEVEL.INFO, "building {} containers".format(len(self.bases)))
        for index, base in enumerate(self.bases):
            build_start = time.time()
            log_info(LOGLEVEL.DEBUG, "{}".format(base.name))

            base_folder_name = "base_{}".format(str(base.base_type).upper())

            # move pwd to the base directory so that COPY commands don't explode
            os.chdir(saved_path)
            os.chdir(os.path.join(self.root_path, base_folder_name))

            # make image
            log(LOGLEVEL.DEBUG, "building")
            cmd = "docker build -t img_{} .".format(base.base_type.lower())
            silent_os_system(cmd)

            log(LOGLEVEL.DEBUG, "creating")
            # make sure only the web base gets exposed
            forwarding_str = " -p{}:80".format(port) if base.base_type.lower() == "web" else ""
            cmd = "docker create --name container_{}{} --network autogen-net img_{}".format(
                base.base_type.lower(), forwarding_str, base.base_type.lower()
            )
            silent_os_system(cmd)

            # files = walk_directory(os.path.join(self.root_path, base_folder_name, "image_files"))
            # log(LOGLEVEL.DEBUG, files)
            # for file in files:
            #     sys_path = os.path.join(self.root_path, base_folder_name, "image_files", file)
            #     #silent_os_system("docker cp {} container_{}:{}".format(sys_path, base.base_type.lower(), file))

            # docker cp is great and lets us just copy each root folder in for free
            log(LOGLEVEL.DEBUG, "trying full copy")
            for f in os.listdir("image_files"):
                silent_os_system(
                    "docker cp {} container_{}:/".format(os.path.join("image_files", f), base.base_type.lower()))

            log(LOGLEVEL.DEBUG, "running")
            silent_os_system("docker start container_{}".format(base.base_type.lower()))

            log(LOGLEVEL.DEBUG, "deleting files")
            for f in walk_directory("image_delete"):
                f_repl = f.replace("\\", "/")
                log(LOGLEVEL.DEBUG,
                    "docker exec -u root container_{} rm -rf /{}".format(base.base_type.lower(), f_repl))
                os.system("docker exec -u root container_{} rm -rf /{}".format(base.base_type.lower(), f_repl))

            # if the container is the WEB container we need to also connect it to the main bridge here
            if base.base_type.lower() == "web":
                silent_os_system("docker network connect bridge container_web")

            build_end = time.time()
            log_info(LOGLEVEL.INFO, "built container {}/{} {}".format(
                index + 1, len(self.bases), timer_format(build_start, build_end)
            ))

        os.chdir(saved_path)

    def is_present(self, name):
        return self.base_present(name) or self.site_present(name) or self.vulnerability_present(name)

    def base_present(self, name):
        return any(b.name == name for b in self.bases)

    def base_type_present(self, base_type):
        return any(b.base_type == base_type for b in self.bases)

    def base_present_fuzzy(self, name):
        return any(name in b.name for b in self.bases)

    def site_present(self, name):
        return self.site.name == name

    def site_present_fuzzy(self, name):
        return name in self.site.name

    def vulnerability_present(self, name):
        return any(v.name == name for v in self.vulns)


def walk_directory(target):
    # walks a directory, returning all files including their full path with respect to target.
    # made because glob.glob() and os.walk() both suck in their own ways
    files = []
    with os.scandir(target) as result:
        entry: os.DirEntry
        for entry in result:
            if entry.is_dir():
                dir_results = [os.path.join(entry.name, f) for f in walk_directory(os.path.join(target, entry.name))]
                files.extend(dir_results)
            else:
                files.append(entry.name)

    return files


def erase_from_directory(target):
    # empties out a directory fully, preserving the directory itself
    with os.scandir(target) as result:
        # pycharm has a bug which means it doesn't recognise the result of os.scandir correctly [ :( ]
        entry: os.DirEntry
        for entry in result:
            if entry.is_dir():
                shutil.rmtree(entry.path)
            else:
                os.remove(entry.path)


def delete_file(path):
    os.remove(path)


def save_full_path(data, dst):
    # Saves data data to dst, creating any folders which do not exist along the way.
    # Use makedirs() with exist_ok=True to create any required folders.
    # Normalize the path before we do this
    dirs, file = os.path.split(dst)
    os.makedirs(dirs, exist_ok=True)

    with open(dst, "w", newline="\n", encoding="utf-8") as f:
        f.write(data)


def copy_full_path(src, dst):
    # Copies file src to dst, creating any folders which do not exist along the way.
    # Use makedirs() with exist_ok=True to create any required folders.
    # Normalize the path before we do this
    dirs, file = os.path.split(dst)
    os.makedirs(dirs, exist_ok=True)

    shutil.copy2(src, dst)


def silent_os_system(cmd):
    if is_debug():
        log_info(LOGLEVEL.DEBUG, " >> {}".format(cmd))
        os.system(cmd)
    else:
        if platform.system() == "Windows":
            os.system(cmd + " 1>nul 2>nul")
        else:
            os.system(cmd + " 1>/dev/null 2>/dev/null")


def timer_format(start, end, str_fmt="(took {} seconds)"):
    return str_fmt.format(round(end - start, 2))


def generate(chosen_difficulty=None, forced_bases=(), forced_site=None, forced_vulns=(), skip_health_check=False):
    start_time = time.time()

    if chosen_difficulty and forced_vulns:
        log_error(
            LOGLEVEL.CRITICAL,
            "A difficulty level and forced vulnerability were supplied at the same time, which are incompatible."
            " Use -h for help."
        )
        return

    if chosen_difficulty and not (0 <= chosen_difficulty <= 100):
        log_error(
            LOGLEVEL.CRITICAL,
            "The difficulty level provided was not within the range of 0 to 100. Use -h for help."
        )
        return

    base_templates: List[BaseTemplate] = []
    site_templates: List[SiteTemplate] = []
    vuln_templates: List[VulnTemplate] = []

    log_info(LOGLEVEL.DEBUG, "loading templates")

    for template_type in ("base", "site", "vulnerability"):
        for tmp_path in os.listdir(os.path.join("templates", template_type)):
            log_info(LOGLEVEL.DEBUG,
                     "loading {} template: {}".format(template_type.replace("vulnerability", "vuln"), tmp_path))
            if template_type == "base":
                template = BaseTemplate(
                    tmp_path, os.path.join("templates", template_type, tmp_path)
                )
                base_templates.append(template)
            elif template_type == "site":
                template = SiteTemplate(
                    tmp_path, os.path.join("templates", template_type, tmp_path)
                )
                site_templates.append(template)
            else:
                template = VulnTemplate(
                    tmp_path, os.path.join("templates", template_type, tmp_path)
                )
                vuln_templates.append(template)

    log_info(LOGLEVEL.DEBUG, "base templates: {}".format(len(base_templates)))
    log_info(LOGLEVEL.DEBUG, "site templates: {}".format(len(site_templates)))
    log_info(LOGLEVEL.DEBUG, "vuln templates: {}".format(len(vuln_templates)))

    if forced_vulns:
        chosen_vulns = []
        for forced_name in forced_vulns:
            possible_matches = list(filter(
                lambda vuln: forced_name.lower() in vuln.name.lower(),
                vuln_templates
            ))

            if len(possible_matches) <= 0:
                log_error(
                    LOGLEVEL.CRITICAL,
                    "A provided vulnerability template (\"{}\") had no matches. Use -h for help.".format(
                        forced_name
                    )
                )
                return

            sorted_matches = sorted(possible_matches, key=lambda v: len(v.name))

            if any(vuln.name == sorted_matches[0].name for vuln in chosen_vulns):
                log_error(
                    LOGLEVEL.CRITICAL,
                    "A provided vulnerability template (\"{}\" => \"{}\") was a duplicate. Use -h for help.".format(
                        forced_name, sorted_matches[0].name
                    )
                )
                return

            # by picking the shortest name, we ensure the fuzzy match can pick anything
            chosen_vulns.append(sorted_matches[0])
    else:
        if chosen_difficulty is not None:
            difficulty_lb = chosen_difficulty - 10
            difficulty_ub = chosen_difficulty + 10

            allowed_vulns = list(filter(
                lambda vuln_template: difficulty_lb <= vuln_template.difficulty < difficulty_ub,
                vuln_templates
            ))

            log_info(LOGLEVEL.DEBUG, "vulns pre-filter: {} ({})".format(
                len(allowed_vulns), ", ".join(
                    v.name for v in allowed_vulns
                )
            ))

            if forced_site:
                # filter by only things compatible with the site
                prev_len = len(allowed_vulns)
                allowed_vulns = list(filter(
                    lambda vuln: forced_site.lower() in vuln.compatible_sites,
                    allowed_vulns
                ))

                log_info(LOGLEVEL.DEBUG, "forced site vuln filter: {} => {}".format(
                    prev_len, len(allowed_vulns)
                ))

            if forced_bases:
                web_base = None
                for base_name in forced_bases:
                    possible_matches = list(filter(
                        lambda base: base_name.lower() in base.name.lower(),
                        base_templates
                    ))

                    if len(possible_matches) <= 0:
                        log_error(
                            LOGLEVEL.CRITICAL,
                            "A provided base template (\"{}\") had no matches. Use -h for help.".format(
                                base_name
                            )
                        )
                        return

                    sorted_matches = sorted(possible_matches, key=lambda v: len(v.name))

                    # by picking the shortest name, we ensure the fuzzy match can pick anything
                    if sorted_matches[0].base_type.lower() == "web":
                        web_base = sorted_matches[0]
                        break

                if web_base:
                    log_info(LOGLEVEL.DEBUG, "forced web base is {}".format(
                        web_base.name
                    ))

                    prev_len = len(allowed_vulns)
                    allowed_vulns = list(filter(
                        lambda vuln: any(compat.lower() in web_base.name.lower() for compat in vuln.compatible_bases),
                        allowed_vulns
                    ))

                    log_info(LOGLEVEL.DEBUG, "forced base vuln filter: {} => {}".format(
                        prev_len, len(allowed_vulns)
                    ))
                else:
                    log_info(LOGLEVEL.DEBUG, "forced bases do not include WEB base")

            log_info(LOGLEVEL.DEBUG, "vulns valid for difficulty {}: {} ({})".format(
                chosen_difficulty, len(allowed_vulns), ", ".join(
                    v.name for v in allowed_vulns
                )
            ))

            if len(allowed_vulns) <= 0:
                log_error(LOGLEVEL.CRITICAL,
                          "The conditions specified meant no vulnerabilities were compatible. Use -h for help.")
                return

            chosen_vulns = [random.choice(allowed_vulns)]
        else:
            log_error(LOGLEVEL.CRITICAL,
                      "No specific vulnerability (-v) nor difficulty (-d) was selected. Use -h for help.")
            return

    log_info(LOGLEVEL.DEBUG, "chosen vulns: ({})".format(", ".join(chosen_vuln.name for chosen_vuln in chosen_vulns)))

    if forced_site:
        possible_matches = list(filter(
            lambda site: forced_site.lower() in site.name.lower(),
            site_templates
        ))

        if len(possible_matches) <= 0:
            log_error(
                LOGLEVEL.CRITICAL,
                "A provided site template (\"{}\") had no matches. Use -h for help.".format(
                    forced_site
                )
            )
            return

        sorted_matches = sorted(possible_matches, key=lambda v: len(v.name))
        chosen_site = sorted_matches[0]
    else:
        # get forced base restrictions if needed
        web_requirement = None
        if forced_bases:
            web_base = None
            for base_name in forced_bases:
                possible_matches = list(filter(
                    lambda base: base_name.lower() in base.name.lower(),
                    base_templates
                ))

                if len(possible_matches) <= 0:
                    log_error(
                        LOGLEVEL.CRITICAL,
                        "A provided base template (\"{}\") had no matches. Use -h for help.".format(
                            base_name
                        )
                    )
                    return

                sorted_matches = sorted(possible_matches, key=lambda v: len(v.name))

                # by picking the shortest name, we ensure the fuzzy match can pick anything
                if sorted_matches[0].base_type.lower() == "web":
                    web_base = sorted_matches[0]
                    break

            if web_base:
                log_info(LOGLEVEL.DEBUG, "forced web base is {}".format(
                    web_base.name
                ))

                web_requirement = web_base.name
            else:
                log_info(LOGLEVEL.DEBUG, "forced bases do not include WEB base")

        possible_sites = []
        for site in site_templates:
            # check if any of vuln's "compatible_sites" fuzzy matches site name
            any_fuzzy_match = all(
                any(compat in site.name for compat in vuln.compatible_sites) for vuln in chosen_vulns
            )

            forced_valid = (web_requirement is None) or (
                any(compat.lower() in web_requirement for compat in site.compatible_bases)
            )

            if any_fuzzy_match and forced_valid:
                log_info(LOGLEVEL.DEBUG,
                         "site {} is valid (match {}, forced {})".format(site.name, any_fuzzy_match, forced_valid))
                possible_sites.append(site)
            else:
                log_info(LOGLEVEL.DEBUG,
                         "site {} is invalid (match {}, forced {})".format(site.name, any_fuzzy_match, forced_valid))

        log_info(LOGLEVEL.DEBUG, "sites valid for vuln: {} ({})".format(
            len(possible_sites), ", ".join(
                v.name for v in possible_sites
            )
        ))

        if len(possible_sites) <= 0:
            log_error(
                LOGLEVEL.CRITICAL,
                "No compatible sites were found under the conditions. Use -h for help."
            )
            return

        chosen_site = random.choice(possible_sites)

    log_info(LOGLEVEL.DEBUG, "chosen site: {}".format(chosen_site.name))

    # even if we specify some bases we need to ensure we generate the rest
    bases_ignore = []
    chosen_bases = []
    if forced_bases:
        for forced_name in forced_bases:
            possible_matches = list(filter(
                lambda base: forced_name.lower() in base.name.lower(),
                base_templates
            ))

            if len(possible_matches) <= 0:
                log_error(
                    LOGLEVEL.CRITICAL,
                    "A provided base template (\"{}\") had no matches. Use -h for help.".format(
                        forced_name
                    )
                )
                return

            sorted_matches = sorted(possible_matches, key=lambda v: len(v.name))

            if sorted_matches[0].base_type.lower() in bases_ignore:
                log_error(
                    LOGLEVEL.CRITICAL,
                    "Too many {} base templates were provided. Use -h for help.".format(
                        sorted_matches[0].base_type.upper()
                    )
                )
                return

            # by picking the shortest name, we ensure the fuzzy match can pick anything
            chosen_bases.append(sorted_matches[0])

            # ignore this type when we go to generate the next
            bases_ignore.append(sorted_matches[0].base_type.lower())

    possible_bases = {}
    needed_bases = set(req.lower() for req in chosen_site.required_bases)
    needed_bases.add("web")
    needed_bases = list(filter(
        lambda basetype: basetype.lower() not in bases_ignore,
        needed_bases
    ))

    log_info(LOGLEVEL.DEBUG, "needed bases: {}".format(", ".join(n.upper() for n in needed_bases)))

    for base in base_templates:
        # add the base if the site requires that type (WEB is always required)
        # and the base matches both the site's compatible_bases and the vuln's compatible_bases
        # (this only applies to web bases)
        if base.base_type.lower() in needed_bases:
            vuln_fuzzy_match = base.base_type.lower() != "web" or all(
                any(compat in base.name for compat in vuln.compatible_bases) for vuln in chosen_vulns
            )

            site_fuzzy_match = base.base_type.lower() != "web" or any(
                compat in base.name for compat in chosen_site.compatible_bases)
            if site_fuzzy_match and vuln_fuzzy_match:
                if base.base_type.upper() in possible_bases:
                    possible_bases[base.base_type.upper()].append(base)
                else:
                    possible_bases[base.base_type.upper()] = [base]

    log_info(LOGLEVEL.DEBUG, "base dict:")

    for base_type in possible_bases:
        if len(possible_bases[base_type]) <= 0:
            log_error(
                LOGLEVEL.CRITICAL,
                "A base template could not be found that satisfies the requirement for a \"{}\" base type. "
                "Use -h for help.".format(
                    base_type.upper()
                )
            )

            return

        log_info(LOGLEVEL.DEBUG, "    {}: [{}]".format(
            base_type, ", ".join(
                b.name for b in possible_bases[base_type]
            )
        ))

    chosen_bases.extend(list(
        random.choice(possible_bases[base_type]) for base_type in possible_bases
    ))
    web_base = next(filter(lambda base: base.base_type.lower() == "web", chosen_bases))

    base_types_available = [
        base.base_type.lower() for base in chosen_bases
    ]

    log_info(LOGLEVEL.DEBUG, "web base: {}".format(web_base.name))
    log_info(LOGLEVEL.DEBUG, "base types: {}".format(
        ", ".join(typ.upper() for typ in base_types_available)
    ))

    for needed in chosen_site.required_bases:
        # if any are missing, sound the alarm
        if not needed.lower() in base_types_available:
            log_error(
                LOGLEVEL.CRITICAL,
                "A base template was not found that satisfies the requirement for a \"{}\" base type. "
                "Use -h for help.".format(
                    needed.upper()
                )
            )

            return

    log_info(LOGLEVEL.DEBUG, "chosen bases:")

    for base in chosen_bases:
        log_info(LOGLEVEL.DEBUG, "    {}: {}".format(
            base.base_type.upper(), base.name
        ))

    # check the list one final time since if we forced templates we might have invalid stuff still
    # what we want to ensure is that our chosen templates do not contradict with each other
    for vuln in chosen_vulns:
        # check vuln has a compatible WEB base and a compatible site
        site_valid = any(compat in chosen_site.name for compat in vuln.compatible_sites)
        bases_valid = any(compat in web_base.name for compat in vuln.compatible_bases)
        if not (site_valid and bases_valid):
            fail_mask = (int(not bases_valid) * 2) + (int(not site_valid)) - 1
            log_error(
                LOGLEVEL.CRITICAL,
                "A vulnerability (\"{}\") is incompatible with the selected {}. Use -h for help.".format(
                    vuln.name,
                    ("site (\"{s}\")", "WEB base (\"{b}\")", "site (\"{s}\") and WEB base (\"{b}\")")[fail_mask].format(
                        s=chosen_site.name, b=web_base.name
                    )
                )
            )
            return

    site_compat = any(compat in web_base.name for compat in chosen_site.compatible_bases)
    site_reqs = all(req.lower() in base_types_available for req in chosen_site.required_bases)
    if not site_compat:
        log_error(
            LOGLEVEL.CRITICAL,
            "The site template (\"{}\") is incompatible with the selected WEB base (\"{}\"). Use -h for help.".format(
                chosen_site.name, web_base.name
            )
        )
        return

    if not site_reqs:
        log_error(
            LOGLEVEL.CRITICAL,
            "The site template (\"{}\") does not have all of its base type requirements filled. Use -h for help.".format(
                chosen_site.name, web_base.name
            )
        )
        return

    if not os.path.exists("staging"):
        os.mkdir("staging")

    log_success(LOGLEVEL.INFO, "template setup and selection finished {}".format(timer_format(start_time, time.time())))

    stage_and_start(chosen_bases, chosen_site, chosen_vulns, start_time, skip_health_check)


def stage_and_start(chosen_bases, chosen_site, chosen_vulns, start_time=0.0, skip_health_check=False):
    if not start_time:
        start_time = time.time()

    port = 9008

    build_start_time = time.time()

    staging_location = StagingLocation("staging/")

    # chosen_bases = [
    #     BaseTemplate("apache2-ubuntu", "templates/base/apache2-ubuntu"),
    #     BaseTemplate("mysql-ubuntu", "templates/base/mysql-ubuntu")
    # ]
    # chosen_site = SiteTemplate("storefront-apache2", "templates/site/imagesite-apache2")
    # chosen_vulns = [VulnTemplate("imagesite-fileupload-htaccess", "templates/vulnerability/imagesite-fileupload-htaccess")]
    # chosen_vulns = []

    for base in chosen_bases:
        staging_location.add(base)

    staging_location.add(chosen_site)

    for vuln in chosen_vulns:
        staging_location.add(vuln)

    log_info(LOGLEVEL.INFO, "staging files")
    staging_location.stage("flag{" + FileAction.random_alnum(32) + "}")

    log_info(LOGLEVEL.INFO, "setting up containers")
    staging_location.setup(port)

    build_end_time = time.time()
    log_success(LOGLEVEL.INFO, "container setup successful {}".format(timer_format(build_start_time, build_end_time)))

    log_info(LOGLEVEL.INFO, "waiting for all containers to start")

    # continually ask for localhost:port until it's up
    t = time.time()
    waiting_response = True
    reqs = 0

    while waiting_response and not skip_health_check:
        x = None
        reqs += 1

        log(LOGLEVEL.DEBUG, "Sending request #{} to http://localhost:{}".format(reqs, port))

        try:
            x = requests.get("http://localhost:{}".format(port), timeout=1)
        except Exception as e:
            pass

        if x and str(x.status_code)[0] not in ("4", "5"):
            waiting_response = False
            finish_time = time.time()
            log(LOGLEVEL.DEBUG, "result status code: {}".format(x.status_code))
            log_success(LOGLEVEL.INFO_QUIET, "Site is up and ready at http://localhost:{} {}".format(
                port, timer_format(start_time, finish_time, "(deployment finished after {} seconds)")
            ))

            for vuln in chosen_vulns:
                if vuln.briefing:
                    log(LOGLEVEL.INFO_QUIET, "challenge briefing: \"{}\"".format(vuln.briefing))

            break
        elif x is not None:
            log(LOGLEVEL.DEBUG, "result status code: {}".format(x.status_code))
        else:
            log(LOGLEVEL.DEBUG, "result is None (probably timeout)")

        if time.time() - t > 100:
            log_failure(LOGLEVEL.INFO_QUIET, "Container health check timed out. Something went wrong.")
            break

        time.sleep(1)

    if skip_health_check:
        log_success(LOGLEVEL.INFO_QUIET, "Finished generation")


def load_base_by_name(template_list, template_name):
    possible_matches = list(filter(
        lambda template: template_name.lower() in template.name.lower(),
        template_list
    ))

    if len(possible_matches) <= 0:
        log_error(
            LOGLEVEL.CRITICAL,
            "A provided base template (\"{}\") had no matches. Use -h for help.".format(
                template_name
            )
        )
        return None

    sorted_matches = sorted(possible_matches, key=lambda v: len(v.name))

    # by picking the shortest name, we ensure the fuzzy match can pick anything
    return sorted_matches[0]


if __name__ == "__main__":
    # hacky way to make windows display ansi (it's been 8 years and i still don't know why it works!)
    os.system("")

    if len(sys.argv) > 1 and sys.argv[1] == "--test-autogen":
        set_loglevel(LOGLEVEL.DEBUG)
        base = BaseTemplate(
            "apache2-ubuntu", os.path.join("templates", "base", "apache2-ubuntu")
        )

        site = SiteTemplate(
            "testautogen-apache2", os.path.join("test-autogen", "template", "testautogen-apache2")
        )

        stage_and_start((base,), site, ())
        exit(0)

    # parse command line args
    set_loglevel(LOGLEVEL.INFO)

    loglevel = LOGLEVEL.INFO
    difficulty = None
    bases = []
    site = None
    vulns = []
    help_chosen = len(sys.argv) == 1
    list_chosen = False
    inspect_chosen = False

    last_arg = ""
    arg_aliases = {
        "--loglevel": "-l",
        "--difficulty": "-d",
        "--base-template": "-b",
        "--site-template": "-s",
        "--vuln-template": "-v",
        "--help": "-h",
        "--inspect": "-i",
        "--list-templates": "--list-templates"
    }

    try:
        for arg in sys.argv[1:]:
            if last_arg:
                if last_arg == "-l":
                    loglevels = (LOGLEVEL.CRITICAL, LOGLEVEL.INFO_QUIET, LOGLEVEL.INFO, LOGLEVEL.DEBUG)
                    if arg.isdigit() and 0 <= int(arg) <= 3:
                        loglevel = loglevels[int(arg)]
                    elif any(arg.upper() == loglvl.name.upper() for loglvl in loglevels):
                        loglevel = next(loglvl for loglvl in loglevels if arg.upper() == loglvl.name.upper())
                    else:
                        log_failure(LOGLEVEL.CRITICAL, "Invalid log level provided ({}).".format(arg))
                        help_chosen = True
                        break

                elif last_arg == "-d":
                    if arg.isdigit() and 0 <= int(arg) <= 100:
                        difficulty = int(arg)
                    else:
                        log_failure(
                            LOGLEVEL.CRITICAL,
                            "Invalid difficulty provided ({}). "
                            "Difficulty must be an integer in the range 0-100.".format(arg)
                        )
                        help_chosen = True
                        break

                elif last_arg == "-b":
                    bases.append(arg)

                elif last_arg == "-s":
                    site = arg

                elif last_arg == "-v":
                    vulns.append(arg)

                elif last_arg == "-h":
                    help_chosen = True

                elif last_arg == "-i":
                    inspect_chosen = True

                elif last_arg == "--list-templates":
                    list_chosen = True

                else:
                    log_failure(
                        LOGLEVEL.CRITICAL,
                        "Invalid parameter ({}).".format(last_arg)
                    )
                    help_chosen = True
                    break

                last_arg = ""
            else:
                if arg.startswith("-") and arg in arg_aliases.values():
                    last_arg = arg
                elif arg.startswith("--") and arg in arg_aliases.keys():
                    last_arg = arg_aliases[arg]
                else:
                    log_failure(
                        LOGLEVEL.CRITICAL,
                        "Invalid parameter ({}).".format(arg)
                    )
                    help_chosen = True
                    break

                if last_arg == "-h":
                    help_chosen = True

                elif last_arg == "-i":
                    inspect_chosen = True

                elif last_arg == "--list-templates":
                    list_chosen = True
    except:
        log_failure(LOGLEVEL.CRITICAL, "Something went wrong processing command line arguments.")
        help_chosen = True

    # print("loglevel:", loglevel)
    # print("difficulty:", difficulty)
    # print("bases:", bases)
    # print("site:", site)
    # print("vulns:", vulns)
    # print("help_chosen:", help_chosen)
    # print("list_chosen:", list_chosen)
    # print("inspect_chosen:", inspect_chosen)
    # print("")

    if help_chosen:
        print("{} [arguments]\n"
              "    -l <value> (--loglevel)      | Changes the log level to one of the following:\n"
              "                                 | CRITICAL   (0) \n"
              "                                 | INFO_QUIET (1) \n"
              "                                 | INFO       (2) \n"
              "                                 | DEBUG      (3) \n"
              "                                 | Note that DEBUG will reveal the templates selected.\n"
              "                                 |\n"
              "    -d <value> (--difficulty)    | Select the difficulty of the randomly chosen vulnerability.\n"
              "                                 |\n"
              "    -b <value> (--base-template) | Add a specific base template to use.\n"
              "                                 | If given multiple times, all provided templates are set as required.\n"
              "                                 |\n"
              "    -s <value> (--site-template) | Set a specific site template to be used for generation.\n"
              "                                 |\n"
              "    -v <value> (--vuln-template) | Set a specific vulnerability template to use. \n"
              "                                 | If given multiple times, all provided templates are set as required.\n"
              "                                 |\n"
              "    -h         (--help)          | Show this help message.\n"
              "                                 |\n"
              "    -i         (--inspect)       | View all information for any selected templates (using -b, -s, -v).\n"
              "                                 |\n"
              "    --list-templates             | List all loaded templates.\n".format(
            sys.argv[0]
        ))
    elif list_chosen:
        base_templates: List[BaseTemplate] = []
        site_templates: List[SiteTemplate] = []
        vuln_templates: List[VulnTemplate] = []

        for template_type in ("base", "site", "vulnerability"):
            for tmp_path in os.listdir(os.path.join("templates", template_type)):
                if template_type == "base":
                    template = BaseTemplate(
                        tmp_path, os.path.join("templates", template_type, tmp_path)
                    )
                    base_templates.append(template)
                elif template_type == "site":
                    template = SiteTemplate(
                        tmp_path, os.path.join("templates", template_type, tmp_path)
                    )
                    site_templates.append(template)
                else:
                    template = VulnTemplate(
                        tmp_path, os.path.join("templates", template_type, tmp_path)
                    )
                    vuln_templates.append(template)

        print("-- Base templates -- ")
        print("\n".join(template.name for template in base_templates))

        print("\n-- Site templates -- ")
        print("\n".join(template.name for template in site_templates))

        print("\n-- Vulnerability templates -- ")
        print("\n".join(template.name for template in vuln_templates))

    elif inspect_chosen:
        base_templates: List[BaseTemplate] = []
        site_templates: List[SiteTemplate] = []
        vuln_templates: List[VulnTemplate] = []

        for template_type in ("base", "site", "vulnerability"):
            for tmp_path in os.listdir(os.path.join("templates", template_type)):
                if template_type == "base":
                    template = BaseTemplate(
                        tmp_path, os.path.join("templates", template_type, tmp_path)
                    )
                    base_templates.append(template)
                elif template_type == "site":
                    template = SiteTemplate(
                        tmp_path, os.path.join("templates", template_type, tmp_path)
                    )
                    site_templates.append(template)
                else:
                    template = VulnTemplate(
                        tmp_path, os.path.join("templates", template_type, tmp_path)
                    )
                    vuln_templates.append(template)

        for base in bases:
            found_base: BaseTemplate = load_base_by_name(base_templates, base)
            print("{}\n"
                  "Base template\n"
                  "{}\n"
                  "Type: {}\n".format(
                found_base.name, found_base.desc, found_base.base_type
            ))

        found_site: SiteTemplate = load_base_by_name(site_templates, site)
        print("{}\n"
              "Site template\n"
              "{}\n"
              "Compatible bases: {}\n"
              "Base types required: {}\n".format(
            found_site.name, found_site.desc,
            ", ".join(b for b in found_site.compatible_bases),
            ", ".join(bt for bt in found_site.required_bases),
        ))

        for vuln in vulns:
            found_vuln: VulnTemplate = load_base_by_name(vuln_templates, vuln)
            print("{}\n"
                  "Vulnerability template\n"
                  "{}\n"
                  "Briefing: {}\n"
                  "Difficulty: {}\n"
                  "Tags: {}\n"
                  "Compatible bases: {}\n"
                  "Compatible sites: {}\n".format(
                found_vuln.name, found_vuln.desc,
                found_vuln.briefing,
                found_vuln.difficulty,
                ", ".join(t for t in found_vuln.tags),
                ", ".join(t for t in found_vuln.compatible_bases),
                ", ".join(t for t in found_vuln.compatible_sites),
            ))
    else:
        set_loglevel(loglevel)
        generate(difficulty, bases, site, vulns)
