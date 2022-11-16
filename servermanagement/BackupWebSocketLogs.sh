# System Variables
# --------------------------------------
LOGFILE_SRC="/usr/local/share/Projects/WritingObserver/Repo-Fork/writing_observer/learning_observer/learning_observer/logs"
LOGFILE_DEST="/usr/local/share/Projects/WritingObserver/Repo-Fork/writing_observer/learning_observer/learning_observer/logs"

# Make the backup name
# ---------------------------------------
LOG_DATE=$(date "+%m-%d-%Y--%H-%M-%S")
BACKUP_NAME="$LOGFILE_DEST/learning_observer_backup_$LOG_DATE.tar.gz"
echo $BACKUP_NAME;

# Create the backup
# ---------------------------------------
echo "Backing up web socket logs"
find $LOGFILE_SRC -name "????-??-??T*.log" -mmin +60 -print0 | tar -czvf $BACKUP_NAME --null -T -
echo "Removing backed up web sockets logs"
find $LOGFILE_SRC -name "????-??-??T*.log" -mmin +120 -delete
