
import logging

from autodeploy.taskapp.celery import app

from .securefile import PrivateKey, PublicKey, KnownHosts, SecureFile

logger = logging.getLogger(__name__)

@app.task
def _dummy_callback(*args, **kwargs):
    return

@app.task
def generate_private_key(environment_id):
    environment = Environment.object.get(pk=environment_id)
    PrivateKey(environment_id).generate('AutoDeploy-' + environment.application.name 
                                            + '-' + environment.name)
    open(KnownHosts(environment_id).get_file_name(), 'w').close()

@app.task
def read_public_key(environment_id):
    environment = Environment.object.get(pk=environment_id)
    return PublicKey(environment_id)