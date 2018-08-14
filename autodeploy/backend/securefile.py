from subprocess import Popen, PIPI, STDOUT
from hashlib import md5
from django.conf import settings
import os


class SecureFileStorage(object):
    """ 存储应用系统的 ssh key """

    def __init__(self, uid):
        self.files = {
            'private_key': PrivateKey(uid),
            'public_key': PublicKey(uid),
            'known_hosts': KnownHosts(uid),
        }

    def __getattr__(self, name):
        return self.files[name]

    def remove(self):
        for _, secure_file in self.files.items():
            secure_file.remore()

class SecureFile(object):
    """ 秘钥的基类 """
    prefix = ''

    def __init__(self, uid):
        if isinstance(uid, int):
            uid = str(uid)
        self.uid = uid
        name_hash = md5(settings.SECURE_KEY + self.prefix + uid).hexdigest()
        self.file_name = os.path.join(settings.PRIVATE_DIR, name_hash)

    def get_file_name(self):
        return self.file_name
    
    def read(self):
        return open(self.file_name, 'r').read()
    
    def remove(self):
        try:
            os.remove(self.file_name)
        except OSError:
            pass

class PrivateKey(SecureFile):
    prefix = 'private_key'

    def generate(self, comment, remove=True):
        if remove:
            Popen(['/bin/rm', '-f', self.get_file_name()]).communicate()

        command = 'ssh-keygen -f {} -C {} -N \'\''.format(self.get_file_name(), comment)
        process = Popen(command,
                        shell=True,
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError('{} failed with code {}'.format(commad, process.returncode))

        command = 'mv {}.pub {}'.format(self.get_file_name(), PublicKey(self.uid).get_file_name())
        process = Popen(command,
                        shell=True,
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = process.communicate()

class PublicKey(SecureFile):
    prefix = 'public_key'

class KnownHosts(SecureFile):
    prefix = 'known_hosts'
                
        