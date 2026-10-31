"""Canonical read-only catalogue shared by API and validation tests."""
from models.software_projects import SOFTWARE_PROJECTS
from models.security_projects import SECURITY_PROJECTS
from models.data_projects import DATA_PROJECTS
from models.azure_projects import AZURE_PROJECTS
from models.gaming_projects import GAMING_PROJECTS

PROJECT_BANKS = dict(software=SOFTWARE_PROJECTS, security=SECURITY_PROJECTS,
                     data=DATA_PROJECTS, azure=AZURE_PROJECTS, gaming=GAMING_PROJECTS)
PROJECTS = {project['id']: project for bank in PROJECT_BANKS.values() for project in bank}

OUTLINE_STARTS = {
    'Plan the core data structures and features',
    'Research the core security concept involved',
    'Source and clean the dataset',
    'Provision the required Azure resources',
    'Set up the game loop and window/rendering',
}

def public_project(project):
    result = dict(project)
    result.pop('mood_fit', None)
    result['plan_quality'] = 'outline' if project['steps'][0] in OUTLINE_STARTS else 'detailed'
    return result
