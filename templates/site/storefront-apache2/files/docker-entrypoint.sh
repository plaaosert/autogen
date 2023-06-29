while ! mysqladmin ping -h"$$BASE["SQL"]$$" --silent; do
    sleep 1
done

mysql -u root -h $$BASE["SQL"]$$ -p$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$ -e "source /tmp/data.sql"

# REPLACE ME TO EDIT DOCKER STARTUP