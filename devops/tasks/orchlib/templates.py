import base64
import uuid
import io
import os.path
import chevron

import orchlib.config

def secure_guid():
    '''
    Mix up a few entropy sources with a few system identifiers...

    This should really be built-in.
    '''
    os_random = str(base64.b64encode(os.urandom(32)))
    uuid1 = uuid.uuid1()
    uuid4 = uuid.uuid4().hex
    return uuid.uuid5(uuid1, uuid4).hex


def render_file_for_transfer(filename, config):
    '''
    This converts a filename and a dictionary into a file-like
    object, ready for upload.
    '''
    with open(filename) as fp:
        return io.StringIO(chevron.render(fp, config))


def upload(
        group,
        machine_name,
        filename,
        remote_filename,
        config,
        username=None,
        permissions=None):
    '''
    This will upload a file to an AWS machine. It will:

    * Find the right file. It might be a system-wide default,
      or a machine-specific one.
    * Generate a set of secure tokens for use in templates (e.g. for
      initial passwords)
    * Render the file through `mustache` templates, based on the
      configuration
    * Upload to the server
    * Move to the right place, and set permissions.
    '''
    # We can use these for security tokens in templates.
    # We should save these at some point
    for i in range(10):
        key = "RANDOM"+str(i)
        if key not in config:
            config["RANDOM"+str(i)] = secure_guid()

    local_filename = orchlib.config.config_filename(machine_name, filename)

    # This seems like an odd place, but latest `fabric` has no way
    # to handle uploads as root.
    group.put(
        render_file_for_transfer(
            local_filename,
            config
        ),
        "/tmp/inv-upload-tmp"
    )

    group.run("sudo mv /tmp/inv-upload-tmp {remote_filename}".format(
        remote_filename=remote_filename,
        mn=machine_name
    ))
    if username is not None:
        group.run("sudo chown {username} {remote_filename}".format(
            username=username,
            remote_filename=remote_filename
        ))
    if permissions is not None:
        group.run("sudo chmod {permissions} {remote_filename}".format(
            permissions=permissions,
            remote_filename=remote_filename
        ))


def download(
        group,
        machine_name,
        filename,
        remote_filename):
    '''
    This will download a configuration file from an AWS machine, as
    specified in the machine configuration. It's a simple parallel
    to `upload`
    '''
    print("Remote file: ", remote_filename)

    local_filename = orchlib.config.config_filename(
        machine_name,
        filename,
        create=True
    )

    print("Local filename: ", local_filename)

    pathname = os.path.split(local_filename)[1]
    if not os.path.exists(pathname):
        os.mkdir(pathname)

    group.get(
        remote_filename,
        local_filename
    )
