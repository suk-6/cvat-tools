import json
from tqdm import tqdm
from utils.cvat import api


class app:
    def __init__(self, params, taskID=None):
        self.API = api(params)
        self.taskID = taskID
        self.taskList = params["taskList"]

        if self.taskID is not None:
            if type(self.taskID) is int:
                self.tasksID = [self.taskID]
            else:
                self.tasksID = self.taskID
        else:
            self.tasks = self.getTasks()
            self.tasksID = self.getTasksID()

        self.jobs = self.API.getJobs()
        self.taskToJob = self.matchTaskToJob()
        self.labels = self.API.getLabels()

        self.counts, self.totals = self.count()
        self.result = self.taskResult()

        self.statistics = self.calcStatistics()

        self.save()

    def matchTaskToJob(self):
        taskToJob = {}
        for job in self.jobs["results"]:
            taskToJob[job["task_id"]] = job["id"]
        return taskToJob

    def getTasks(self):
        tasks = []
        if self.taskList is not None:
            with open(self.taskList, "r") as f:
                self.taskList = [name for name in f.read().split("\n") if name != ""]
            for task in self.API.getTasks()["results"]:
                if task["name"] in self.taskList:
                    tasks.append(task)
                    self.taskList.remove(task["name"])
            if len(self.taskList) > 0:
                print(f"Task(s) not found: {self.taskList}")
        else:
            tasks = self.API.getTasks()["results"]
        return tasks

    def getTasksID(self):
        tasksID = []
        for task in self.tasks:
            tasksID.append(task["id"])
        return tasksID

    def sumObject(self, obj):
        total = 0

        for key in obj:
            total += obj[key]

        return total

    def initCount(self):
        counts = {}

        for label in self.labels.values():
            counts[label] = 0

        return counts

    def count(self):
        counts = {}
        totals = {}

        for id in tqdm(self.tasksID):
            count = self.initCount()
            annotations = self.API.getAnnotation(self.taskToJob[id])
            try:
                for annotation in annotations["shapes"]:
                    label = self.labels[annotation["label_id"]]
                    count[label] += 1
            except:
                pass

            try:
                for track in annotations["tracks"]:
                    label = self.labels[track["label_id"]]
                    count[label] += (
                        track["shapes"][-1]["frame"] - track["shapes"][0]["frame"]
                    )
            except:
                pass

            total = self.sumObject(count)

            counts[id] = count
            totals[id] = total

        return counts, totals

    def taskResult(self, id=None):
        result = {}
        if id is not None:
            result[id] = {}
            result[id]["jobID"] = self.taskToJob[id]
            result[id]["count"] = self.counts[id]
            result[id]["total"] = self.totals[id]
        else:
            for id in self.tasksID:
                result[id] = {}
                result[id]["jobID"] = self.taskToJob[id]
                result[id]["count"] = self.counts[id]
                result[id]["total"] = self.totals[id]
        return result

    def calcStatistics(self):
        count = self.initCount()
        total = 0

        for id in self.result:
            for label in count.keys():
                count[label] += self.result[id]["count"][label]
            total += self.result[id]["total"]

        print("Total: ", total)
        print("Count: ", count)

        return {"count": count, "total": total}

    def save(self):
        saveData = {}
        saveData["statistics"] = self.statistics
        saveData["result"] = self.result

        with open("result.json", "w") as f:
            json.dump(saveData, f, indent=4)


if __name__ == "__main__":
    from utils.config import loadConfig

    params = loadConfig()

    app = app(params)
