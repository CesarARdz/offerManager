import os
from dropbox.client import DropboxClient
from dropbox.datastore import DatastoreManager, DatastoreConflictError
from bottle import route, request, static_file, run
from config import DROPBOX_TOKEN, IMAGES_PATH, MAX_RETRIES
from Logger import _logger

@route('/')
def root():
    return static_file('index.html', root='.')


@route('/upload', method='POST')
def do_upload():
    begin = request.forms.get('beginDate')
    end = request.forms.get('endDate')
    upload = request.files.get('upload')

    if upload is not None:
        raw = upload.file.read()
        path = saveOnDisk(upload.filename, raw)
        saveOnDropbox(path, upload.filename, begin, end)
    else:
        return "Need to select an image, try again."
    return "Upload Sucessful"


def saveOnDropbox(full_path, filename, begin, end):
    client = DropboxClient(DROPBOX_TOKEN)
    manager = DatastoreManager(client)
    datastore = manager.open_default_datastore()

    offer_table = datastore.get_table('offers')
    for _ in range(MAX_RETRIES):
        try:
            first_offer = offer_table.insert(offerName=filename, begin=begin, end=end)
            datastore.commit()
            _logger.debug("data saved on offers table = (%s, %s, %s)" % (filename, begin, end))
            break
        except DatastoreConflictError:
            datastore.rollback()    # roll back local changes
            datastore.load_deltas()  # load new changes from Dropbox

    image = open(full_path, 'rb')
    response = client.put_file(filename, image)
    image.close()

    _logger.debug("%s saved on dropbox" % filename)

def saveOnDisk(filename, upload):
    if not os.path.exists(IMAGES_PATH):
        os.makedirs(IMAGES_PATH)

    file_path = IMAGES_PATH + filename

    image = open(file_path, 'wb')
    image.write(upload)
    image.close()
    _logger.debug("%s saved on disk" % file_path)

    return file_path

if __name__ == '__main__':
    run(host='localhost', port=8086)
