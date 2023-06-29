while ! mysqladmin ping -h"$$BASE["SQL"]$$" --silent; do
    sleep 1
done

chmod 777 /var/www/html/uploads

chmod 777 /tmp/

mysql -u root -h $$BASE["SQL"]$$ -p$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$ -e "source /tmp/data.sql"

# REPLACE ME TO EDIT DOCKER STARTUP