#this is to communicate with the database
def individual_data(todo): #this is the only data set we will get when we fetch data from the db
    return {
        "id" : str(todo["_id"]),
        "title": todo["title"],
        "description": todo["description"],
        "status": todo["is_completed"]
    }

#the list data - all the data into document - after this func its gonna create the individual_data dict
def all_tasks(todos):
    return [individual_data(todo)for todo in todos]
