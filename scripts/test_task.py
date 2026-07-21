from agents.base.task import Task

task = Task(
    name="Open Browser",
    description="Launch Brave Browser",
    data={
        "browser": "Brave"
    }
)

print(task)