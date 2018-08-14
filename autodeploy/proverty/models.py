from django.db import models
import pgcrypto
from django.db.models.signals import post_save, post_delete
from django.urls import reverse
from django.core.validators import RegexValidator
from datetime import datetime, timedelta

def autodeploy_name():
    return RegexValidator(regex='^[a-zA-Z0-9_\.\-]+$', message='存在非法字符')

class Department(models.Model):
    name = models.CharField(blank=False, max_length=128, validators=[autodeploy_name()]
                            , unique=True)
    
    class Meta:
        ordering = ['name']
        permissions = (
            ("view_department", "Can view department"),
            ("execute_department", "Can execute department"),
        )

    def __str__(self):
        return self.name

class Application(models.Model):
    name = models.CharField(blank=False, max_length=128, validators=[autodeploy_name()])
    department = models.ForeignKey(Department, related_name="applications", on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']
        unique_together = ("department", "name")
        permissions = (
            ("viwe_application", "Can view application"),
            ("execute_aaplication", "Can execute application"),
        )

    def get_absolute_url(self):
        return reverse('application_page', args=[str(self.id)])
    
    def executions_inline(self):
        from task.models import executions_inline
        return Execution.get_inline_by_application(self.id)

class Environment(models.Model):
    name = models.CharField(blank=False, max_length=128, validators=[autodeploy_name()])
    application = models.ForeignKey(Application, related_name='environments', on_delete=models.CASCADE)
    is_production = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        unique_together = ("application", "name")
        permissions = (
            ("view_environment", "Can view environment"),
            ("execute_environment", "Can execute environment"),
        )

    def get_absolute_url(self):
        return reverse('environment_page', args=[str(self.id)])

    def executions_inline(self):
        from task.models import Execution
        return Execution.get_inline_by_environment(self.id)

    @staticmethod
    def generate_keys(sender, instance, created, **kwargs):
        if created:
            from backend.tasks import generate_private_key
            generate_private_key.delay(environment_id=instance.id)

    @staticmethod
    def cleanup_files(sender, instance, **kwargs):
        from backend.tasks import cleanup_files
        cleanup_files.delay(instance.id)

    def stats_count(self):
        return self.application.tasks.\
            filter(executions__environment=self).\
            annotate(avg=models.Avg('executions__time'), count=models.Count('executions'))

    def stats_status(self):
        return self.executions.\
            filter(time_start__gte=datetime.now()-timedelta(days=30)).\
            values('status').\
            annotate(count=models.Count('status'))

post_save.connect(Environment.generate_keys, sender=Environment)
post_delete.connect(Environment.cleanup_files, sender=Environment)

class ServerRole(models.Model):
    name = models.CharField(blank=False, max_length=32, validators=[autodeploy_name()])
    department = models.ForeignKey(Department, related_name="serverroles", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("department", "name")

    def __str__(self):
        return self.name
        
    @staticmethod
    def on_create_department(sender, instance, created, **kwargs):
        for server_role in ['app', 'db', 'was']:
            ServerRole(name=server_role, department=instance).save()

post_save.connect(ServerRole.on_create_department, sender=Department)

class Server(models.Model):
    OPENSSH_PASSWORD = 1
    OPENSSH_CERTIFICATE = 2
    METHOD_CHOICE = (
        (OPENSSH_CERTIFICATE, 'SSH certificate'),
        (OPENSSH_PASSWORD, 'SSH password'),
    )

    name = models.CharField(blank=False, max_length=128, validators=[autodeploy_name()])
    host = models.CharField(blank=False, max_length=128)
    port = models.IntegerField(blank=False)
    roles = models.ManyToManyField(ServerRole, related_name="servers")
    environment = models.ForeignKey(Environment, related_name="servers", on_delete=models.CASCADE)
    method = models.IntegerField(choices=METHOD_CHOICE, default=OPENSSH_CERTIFICATE,
                verbose_name='Login method')
    
    class Meta:
        unique_together = ("environment", "name")
        ordering = ['name']

class ServerAuthentication(models.Model):
    server = models.OneToOneField(Server, primary_key=True, on_delete=models.CASCADE)
    password = pgcrypto.EncryptedTextField(blank=True)