# project.py
class Project:
    def __init__(self, project_id, project_name, project_desc,
                 members_list=None, num_of_hardware_sets=0,
                 hardware_set_id=None):

        self.project_id = project_id
        self.project_name = project_name
        self.project_desc = project_desc
        self.members_list = members_list or []
        self.num_of_hardware_sets = num_of_hardware_sets
        self.hardware_set_id = hardware_set_id or []

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "project_desc": self.project_desc,
            "members_list": self.members_list,
            "num_of_hardware_sets": self.num_of_hardware_sets,
            "hardware_set_id": self.hardware_set_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            project_id=data.get("project_id"),
            project_name=data.get("project_name"),
            project_desc=data.get("project_desc"),
            members_list=data.get("members_list", []),
            num_of_hardware_sets=data.get("num_of_hardware_sets", 0),
            hardware_set_id=data.get("hardware_set_id", []),
        )

