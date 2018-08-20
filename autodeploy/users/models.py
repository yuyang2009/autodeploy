from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db.models.signals import post_save
from guardian.shortcuts import assign_perm
from django.db import models
from django.contrib.auth.models import AbstractUser
# from task.models import Task

class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    REQUIRED_FIELDS = ['name']

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

# class MyCustomUserManger(BaseUserManager):
#     def create_user(self, username, password=None, **extra_fields):
#         if not username:
#             raise ValueError('The given username must be set')
#         user = self.model(username = username, is_active=True,
#                           last_login=now, date_joined=now, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
    
#     def create_superuser(self, username, password, **extra_fields):
#         user = self.create_user(email, password=password, **extra_fields)
#         user.is_admin = True
#         user.save(using=self._db)
#         return user

# class MyCustomUser(AbstractUser, PermissionsMixin):
#     username = models.CharField('notes id', max_length=254, unique=True)
#     name = models.CharField('name', max_length=30, blank=True)
#     is_active = models.BooleanField('active', default=True)
#     is_admin = models.BooleanField(default=False)
#     date_joined = models.DateTimeField('date joined', default=timezone.now)

#     objects = MyCustomUserManger()
#     timezone = TimeZoneField(default='UTC')

#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['name']

#     class Meta:
#         verbose_name = 'account'
#         verbose_name_plural = 'accounts'

#     def get_absolute_url(self):
#         return reverse('users:detail', kwargs={"username": self.username})
    
#     def get_full_name(self):
#         if self.name:
#             return self.name
#         else:
#             return self.username
    
#     def get_short_name(self):
#         return self.name
    # def email_user(self, subject, message, from_email=None):
    #     send_mail(subject, message, from_email, [self.email])

from django.contrib.auth.models import Group
from autodeploy.proverty.models import Department, Application, Environment

class DepartmentGroup(Group):
    department = models.ForeignKey(Department, related_name='groups', on_delete=models.CASCADE)
    local_name = models.CharField(max_length=124)
    system_name = models.CharField(max_length=12)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        self.name = "{}_{}".format(self.department_id, self.local_name)
        super(DepartmentGroup, self).save(*args, **kwargs)

    def assign_department_perms(self, department):
        assign_perm('proverty.view_department', self, department)

    @staticmethod
    def on_create_department(sender, instance, created, **kwargs):
        if created:
            for system_name, group_name in settings.DEFAULT_DEPARTMENT_GROUPS.items():
                group = DepartmentGroup(department=instance, local_name=group_name, system_name=system_name)
                group.save()
                DepartmentGroup.assign_department_perms(group, instance.application.department, )
                if system_name == 'admin':
                    assign_perm('proverty.change_department', group, instance)

    @staticmethod
    def on_create_application(sender, instance, created, **kwargs):
        if created:
            DepartmentGroup._assign_default_perms('proverty', 'application', 
                instance.department, instance)
    
    @staticmethod
    def on_create_environment(sender, instance, created, **kwargs):
        if created:
            DepartmentGroup._assign_default_perms('proverty', 'environment', 
                instance.application.department)

    # @staticmethod
    # def on_create_task(sender, instance, created, **kwargs):
    #     if created:
    #         DepartmentGroup._assign_default_perms('task', 'task', instance.application.department,
    #             instance)

    @staticmethod
    def _assign_default_perms(app, model, department, instance):
        groups = DepartmentGroup.objects.filter(department=department, 
                                                system_name__in=['user', 'admin',])
        for group in groups:
            for action in ['view', 'execute']:
                assign_perm("{}.{}_{}".format(app, action, model), group, instance)
            if group.system_name == 'admin':
                assign_perm("{}.{}_{}".format(app, 'change', model), group, instance)
        
    def __str__(self):
        return self.local_name

post_save.connect(DepartmentGroup.on_create_department, sender=Department)
post_save.connect(DepartmentGroup.on_create_application, sender=Application)
post_save.connect(DepartmentGroup.on_create_environment, sender=Environment)
# post_save.connect(DepartmentGroup.on_create_task, sender=Task)
