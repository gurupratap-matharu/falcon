#!/usr/bin/env bash
#
# Compress and gzip the entire folder and upload to cloud
#
DATE_TIME=$(date "+%Y-%m-%dT%H:%M:%S%Z")

BACKUP_FILE="falcon_${DATE_TIME}.tar.gz"
BACKUP_LOCATION=/tmp/$BACKUP_FILE
B2_BUCKET=ventanita
B2_TARGET=backups/$BACKUP_FILE

echo "Backing up falcon to $BACKUP_LOCATION..."

tar --exclude-vcs --exclude=__pycache__ --exclude=media/ --exclude=__pycache__ --exclude=.ruff_cache --exclude=htmlcov -cvzf $BACKUP_LOCATION ~/Desktop/code/apps/django-apps/falcon


echo "Copying $BACKUP_LOCATION to $B2_BUCKET/$B2_TARGET"
/usr/local/bin/b2 file upload $B2_BUCKET $BACKUP_LOCATION $B2_TARGET
echo "Backup completed"


# BACKUP_RESULT=$(/usr/local/bin/b2 ls --recursive --with-wildcard "b2://$B2_BUCKET/*.gz" | tail -n 1)
# echo "Latest B2 backup is $BACKUP_RESULT"
