import os
from dropbox.client import DropboxClient
from dropbox.datastore import DatastoreManager, DatastoreConflictError
from bottle import route, request, static_file, run, template, TEMPLATE_PATH
from config import DROPBOX_TOKEN, IMAGES_PATH, MAX_RETRIES
from Logger import _logger
import datetime

@route('/')
def root():
    return static_file('pages/index.html', root='.')

@route('/delete')
def root():
    return static_file('pages/delete.html', root='.')

@route('/deleteRecord', method='POST')
def do_delete():
    deleteR()
    return "All Records delete"


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

@route('/activationForm')
def root():
    return static_file('pages/index2.html', root='.')

@route('/activation', method='POST')
def do_uploadData():
    phone = request.forms.get('phone')
    serial = request.forms.get('serial')
    date = request.forms.get('instDate')
    instalation = request.forms.get('onoffswitch')

    saveDataOnDropbox(phone, serial, date, instalation)
    return "Upload Data Sucessful"

@route('/galeria', method='GET')
def genera_galeria():
    return static_file('pages/galeria.tpl', root='.')

@route('/images/<filename:path>', method='GET')
def serve_files(filename):
    return static_file(filename, root='images/')


@route('/get_images', method='GET')
def get_images_of_this_month():
    client = DropboxClient(DROPBOX_TOKEN)
    manager = DatastoreManager(client)
    datastore = manager.open_default_datastore()

    offer_table = datastore.get_table('offers')
    offers = offer_table.query()

    images_to_show = []
    for offer in offers:  # dropbox.datastore.Record
        name = offer.get('offerName')
        begin = datetime.datetime.strptime(offer.get('begin'), "%Y-%m-%d").date()
        end = datetime.datetime.strptime(offer.get('end'), "%Y-%m-%d").date()
        begin_month = '{:02d}'.format(begin.month)
        end_month = '{:02d}'.format(end.month)
        current_month = '{:02d}'.format(datetime.datetime.now().month)
        year = '{:4d}'.format(datetime.datetime.now().year)
        if current_month == begin_month or current_month == end_month:
            # belong to the current month, so we show it
            images_to_show.append(name)

    images_paths = download_and_save_images(images_to_show, year, current_month)

    TEMPLATE_PATH.insert(0,'pages/')
    return template('galeria', images=images_paths)

def download_and_save_images(list_images, year, month):
    client = DropboxClient(DROPBOX_TOKEN)
    DESTINATION_FOLDER = 'images/' + year + month + '/'
    if not os.path.exists(DESTINATION_FOLDER):
        os.makedirs(DESTINATION_FOLDER)
    final_images = []
    for image in list_images:
        f, metadata = client.get_file_and_metadata(image)
        out = open(DESTINATION_FOLDER + image, 'wb')
        final_images.append(DESTINATION_FOLDER + image)
        out.write(f.read())
        out.close()
    return final_images

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

def saveDataOnDropbox(phone, serial, date, instalation):
    client = DropboxClient(DROPBOX_TOKEN)
    manager = DatastoreManager(client)
    datastore = manager.open_default_datastore()

    devices_table = datastore.get_table('uk_devices')
    for _ in range(MAX_RETRIES):
        try:
            first_offer = devices_table.insert(phoneNumber=phone, serialNumber=serial, dateActivate=date, instStatus=instalation)
            datastore.commit()
            _logger.debug("data saved on offers table = (%s, %s, %s, %s)" % (phone, serial, date, instalation))
            break
        except DatastoreConflictError:
            datastore.rollback()    # roll back local changes
            datastore.load_deltas()  # load new changes from Dropbox

def deleteR():
    client = DropboxClient(DROPBOX_TOKEN)
    manager = DatastoreManager(client)
    datastore = manager.open_default_datastore()
    tasks_table = datastore.get_table('uk_devices')
    tasks = tasks_table.query(instStatus='on')
    for task in tasks:
        print task.get('serialNumber')
        task.delete()
    datastore.transaction(deleteR, max_tries=4)
    datastore.commit()


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
