import config
from celery import Celery 
from celery.utils.log import get_task_logger
import dropbox 
import clamd


celery = Celery(
    'worker',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

celery_logger = get_task_logger(__name__)

# clamd init
celery_logger.info('initializing Clamav')
try:
  cd = clamd.ClamdUnixSocket()
  cd.ping()
except:
  celery_logger.info('could not open clamd unix socket. attemping network socket')
  cd = clamd.ClamdNetworkSocket()
  try:
    cd.ping()
  except clamd.ConnectionError:
    celery_logger.info('could not connect to clamd server either by unix or network socket. go big or go home I guess.')
    cd = None 

# dropbox init
celery_logger.info('initializing Dropbox')
dbx = dropbox.Dropbox(config.DROPBOX_ACCESS_TOKEN)

def has_virus(file_path):
  if cd is None:
    return False 
  celery_logger.info('scanning for viruses')
  result = cd.scan(os.path.abspath(file_path))
  celery_logger.info('scanned for viruses')
  celery_logger.info('scan results: %s, %s' % (result[os.path.abspath(file_path)][0], result[os.path.abspath(file_path)][1]))
  return result[os.path.abspath(file_path)][1] is not None 

def save_to_dropbox(file_path):
  # TODO work on this
  celery_logger.info('saving to dropbox')
  with open(os.path.abspath(file_path), 'rb') as file:
    contents = file.read()
    dbx.files_upload(contents, '/' + ntpath.basename(file_path))

@celery.task()
def process_file(file_path):
  celery_logger.info('processing %s' % ntpath.basename(file_path))
  
  if not has_virus(file_path):
    save_to_dropbox(file_path)
  else:
    celery_logger.info('%s is suspected to be a virus. deleting' % ntpath.basename(file_path))