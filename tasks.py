from invoke import task

@task
def install(c):
    c.run("playwright install")