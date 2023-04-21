docker exec mongo sh -c "exec mongodump -d mydb --archive" > /opt/mongoBackUp/all-collections.archive

cd /opt/mongoBackUp

git commit -a -m "`date`"

git push

#git push 'https://{acc}:{password}@gitlab.com/jerry0644/mongobackup.git'
