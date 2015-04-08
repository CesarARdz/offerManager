
import os
import dropbox
from bottle import route, request, static_file, run
from dropbox.datastore import DatastoreError, DatastoreManager, Date, Bytes

guardar_en_dropbox = True

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
        filename = upload.filename

        ruta, archivo = guardar_en_compu(filename, raw)

        if guardar_en_dropbox:
            guardar_en_dropbox(ruta, archivo, begin, end)
    return "Upload Sucessful"

def guardar_en_dropbox(ruta, archivo, begin, end):

    client = dropbox.client.DropboxClient('5b5NpEV9XJsAAAAAAAAW2nNGX11Iw8Q56my4UT3ukZeBjdYFukZtynCQ_r1S51MC')

    manager = DatastoreManager(client)
    datastore = manager.open_default_datastore()

    offer_table = datastore.get_table('offers')
    for _ in range(4):
        try:
            first_offer = offer_table.insert(offerName=archivo, begin=begin, end=end)
            datastore.commit()
            break
        except DatastoreConflictError:
            datastore.rollback()    # roll back local changes
            datastore.load_deltas() # load new changes from Dropbox

    f = open(ruta, 'rb')
    response = client.put_file(archivo, f)
    f.close()

def guardar_en_compu(filename, upload):
    name, ext = os.path.splitext(filename)
    if ext not in ('.png', '.jpg', '.jpeg'):
        return "File extension not allowed."

    save_path = "tmp"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    file_path = "{path}/{file}".format(path=save_path, file=filename)

    salida = open(file_path, 'wb')
    salida.write(upload)
    salida.close()
    return file_path, filename

if __name__ == '__main__':
    run(host='localhost', port=8086)
