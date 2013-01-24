import sys
import os
from pyactiveresource.activeresource import ActiveResource
from pyactiveresource.connection import ResourceNotFound, MethodNotAllowed
import urlparse


class RedmineResource(ActiveResource):
    def __init__(self, attributes=None, prefix_options=None):
        if isinstance(attributes, basestring):
            self.name = attributes
        super(RedmineResource, self).__init__(attributes, prefix_options)

    def dump(self, indent=2):
        ind = ' ' * indent
        for name, value in self.attributes.items():
            if not isinstance(value, RedmineResource):
                if not isinstance(value, list):
                    value = [value]
                for v in value:
                    if isinstance(v, RedmineResource):
                        print ind, name + ':'
                        v.dump(indent + 2)
                        print ind, '---'
                    else:
                        print ind, name, '=', value
            else:
                print ind, name + ':'
                value.dump(indent + 2)
                print ind, '---'


class Project(RedmineResource): pass

class Issue(RedmineResource): pass

class Group(RedmineResource): pass

class User(RedmineResource): pass

class Membership(RedmineResource): pass

class Role(RedmineResource): pass

class Version(RedmineResource): pass

class IssueCategory(RedmineResource): pass

class TimeEntry(RedmineResource): pass

class Permission(RedmineResource):
    def __repr__(self):
        return '%s(%s)' % (self._singular, self.name)

class CustomField(RedmineResource):
    def __repr__(self):
        return '%s(%s)' % (self._singular, self.name)




class RedmineException(Exception): pass


class RedmineClient(object):

    def __init__(self, api_key, url, login, password):
        RedmineResource.site = url
        if api_key is not None:
            RedmineResource.headers = {'X-Redmine-API-Key': api_key}
        else:
            self._user = login
            self._password = password
            RedmineResource.user = login
            RedmineResource.password = password
        Membership.prefix_source += '/projects/$project_id'

    @property
    def headers(self):
        headers = {}
        if RedmineResource.headers:
            for name, value in RedmineResource.headers.items():
                headers[name] = value
        if RedmineResource.connection.auth:
            headers['Authorization'] = 'Basic ' + RedmineResource.connection.auth
        return headers

    def get_project(self, project_id):
        try:
            return Project.find(project_id)
        except ResourceNotFound:
            raise RedmineException(
                "Project '%s' doesn't exist in Redmine" % project_id)

    def get_projects(self, project_ids=None):
        if project_ids:
            return [self.get_project(id_) for id_ in project_ids]
        return Project.find()


    def get_issues(self, project_id=None):
        return Issue.find(None, None, project_id=project_id)

    def get_issue_details(self, issue_id):
        return Issue.find(issue_id,
            include='journals,assigned_to_id,attachments,children,relations')

    def get_project_issues(self, _id, _limit=None, _offset=None):
        return_data = []
        if _limit:
            if _offset is None:
                _offset = 0
            issues = Issue.find(None, None, project_id=_id,
                                limit=_limit, offset=_offset, sort='id')
        elif _offset:
            issues = Issue.find(None, None, project_id=_id,
                                offset=_offset, sort='id')
        else:
            issues = Issue.find(None, None, project_id=_id, sort='id')
        for issue_id in [issue.id for issue in issues]:
            return_data.append(self.get_issue_details(issue_id))
        return return_data
        

    def get_user(self, user_id):
        return User.find(user_id, None, include='groups')

    def get_users(self, user_ids=None):
        if user_ids:
            return [self.get_user(uid) for uid in user_ids]
        return User.find(None, None, include='groups')

    def get_groups(self):
        return Group.find()

    def get_project_members(self, id_):
        return Membership.find(None, None, project_id=id_)


    def get_roles(self):
        roles = Role.find()
        for role in roles:
            try:
                role.attributes['permissions'] = Role().find(role.id).permissions
            except (ResourceNotFound, MethodNotAllowed):
                print "WARN: Can't get permissions for roles."
                print "WARN: This Redmine version doesn't support this feature."
                break
        return roles

    def get_category(self, id_):
        return IssueCategory.find(id_)

    def get_version(self, id_):
        return Version.find(id_)

    def get_time_entries(self, issue_id):
        return TimeEntry.find(None, None, issue_id=issue_id)
