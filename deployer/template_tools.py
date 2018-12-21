
import os
import sys
from invoke import Exit
import jinja2
from jinja2.exceptions import TemplateSyntaxError
import yaml

def fill_templates(config):
    """
    Inspect `secrets.yml` in the working tree and replace the 
    placeholders contained in the files described with actual 
    secrets.
    """
    basedir = config.get_working_tree()
    secrets = config.get_secrets_file_name() 
    if secrets is None:
        return
    secrets_path = os.path.join(basedir, secrets)
    if not os.path.exists(secrets_path):
        raise Exit("Secrets file '{}' does not exist.".format(secrets_path))
    jinja2_env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
    with open(secrets_path, "r") as f:
        doc = yaml.load(f)
    for fname, info in doc['files'].items():
        path = os.path.join(basedir, fname)
        with open(path) as f:
            try:
                t = jinja2_env.from_string(f.read())
            except Exception as ex:
                fabutils.warn("Error processing template '{0}'.".format(path))
                raise
            transformed = os.path.splitext(path)[0]
            with open(transformed, "w") as fout:
                print(t.render(info['secrets']), file=fout)

