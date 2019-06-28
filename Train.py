import threading
import time
import requests
import json


class Train(object):
    """ 
    A class representing a Train object

    ...

    Attributes
    ----------
    time_remaining: int
        An integer representing the time of departure.
    train_type: str
        A description of the train destination (lunch, drinks, meeting, etc).
    display_destination: str
        Train destination (as submitted).
    map_destination: str
        Train destination (lowercase).
    passengers: str
        A set containing names of all users who have boarded the train.
    lock: obj
        A threading object to prevent simultaneous access to the train.

    Methods
    -------
    add_passenger(passenger)
        Adds a passenger to the train
    passenger_string
        Concatenates and announces names of all current train passengers
    """

    def __init__(self, conductor, train_type, destination, departure_time):
        """
        Parameters
        ----------
        time_remaining: int
            An integer representing the time of departure.
        train_type: str
            A description of the train destination (lunch, drinks, meeting, etc).
        display_destination: str
            Train destination (as submitted).
        map_destination: str
            Train destination (lowercase).
        passengers: str
            A set containing names of all users who have boarded the train.
        lock: obj
            A threading object to prevent simultaneous access to the train.
        """

        self.time_remaining = departure_time
        self.train_type = train_type
        self.display_destination = destination
        self.map_destination = destination.lower()
        self.passengers = set([conductor])
        self.lock = threading.Lock()

    def add_passenger(self, passenger):
        """Adds the user as a passenger to the Train
        
        The passenger name will be taken from the interacting user's username 
        If the user is already aboard the train, the user will be notified
        and no changes will be made to the Train.

        Parameters
        ----------
        passenger: str
            Name of passenger to board the train
        """

        self.lock.acquire()                 # Check the Train out for modification
        if passenger in self.passengers:
            self.lock.release()             # Check the Train back in to allow access by others
            return "%s is already on the train to %s" % (passenger, self.display_destination)
        self.passengers.add(passenger)      # Add the user to the set of passengers
        self.lock.release()
        return None

    def passenger_string(self):
        """Concatenates a string listing all passengers aboard the train"""        

        self.lock.acquire()
        res = ""
        passenger_count = len(self.passengers)
        i = 0
        for passenger in self.Passengers:
            res += passenger
            if i != passenger_count - 1:
                res += ", "
            if i == passenger_count - 2:
                res += "and "
            i += 1
        self.lock.release()
        return res
    
    def __str__(self):
        return 'A train to %s at %s' % self.display_destination, self.departure_time


class Station(object):
    """ 
    A class representing a Station object

    ...

    Attributes
    ---------
    lock: obj
        A threading object to prevent simultaneous access to the station.
    trains: dict
        A dictionary containing all train objects, identified by their map_destination

    Methods
    -------
    add_train(train)
        Adds a train to the station
    delete_train(train)
        Remove a train from the station
    list_active_trains()
        Lists all active trains
    help()
        Displays /train usage
    join_train(passenger, destination)
        Adds the user to the train going to the specified destination 
    disembark_train(passenger, destination)
        Removes user from specified train
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.trains = {}

    def add_train(self, train):
        """Adds a new train to the station's train dictionary.
        
        If there is already a train to the specified destination
        The user will be notified and no new train will be added

        Parameters
        ----------
        train: obj 
           A train object 
        """

        if train.map_destination in self.trains: return "There's already a train to %s" % train.map_destination
        else:
            self.trains[train.map_destination] = train
            return None

    def delete_train(self, destination):
        """Removes a train from the station's train dictionary.
        
        If the selected destination does not exist in the train dictionary
        The user will be notified and no change will be made

        Parameters
        ----------
        destination: str
            The train destination passed as the existing map_destination
        """
        res = self.trains.pop(destination, None)
        if res is None:
            return res
        return "The train to %s doesn't exist so it can't be removed" % destination

    def list_active_trains(self):
        """Lists all active trains"""

        self.lock.acquire()
        res = "There are trains to: "
        i = 0
        train_count = len(self.trains)
        if train_count == 0:
            self.lock.release()
            return "There are currently no active trains"
        for dest in self.trains:
            train = self.trains[dest]
            if train_count == 1:
                self.lock.release()
                return "There is currently a train to %s in %d mins (with %s on it)" % (train.display_destination, train.time_remaining, train.passenger_string())
            else:
                res += "%s in %d mins (with %s on it)" % (train.display_destination, train.time_remaining, train.passenger_string())
            if i != train_count - 1:
                res += ", "
            if i == train_count - 2:
                res += "and "
            i += 1
        self.lock.release()
        return res

    def help(self):
        # TODO: Incorporate train types 
        """Lists standard usage for the /train command"""

        return ":steam_locomotive: Need some help with `/train`?\n
        To start a new train:\n
        `/train start <destination> <departure_time>`\n\n

        To join an existing train:\n
        `/train join <destination>`\n\n

        To list all active trains:\n
        `/train active`\n\n"
        
        # TODO: Change destination
        "To change an existing train's destination\n
        `/train reroute <old_destination> <new_destination>`\n\n"

        # TODO: Change departure time
        "To change an existing train's departure time\n 
        `/train reschedule <destination> <new_departure_time>`"

    def join_train(self, passenger, destination):
        """Add user to an existing train

        If there is no train going to the specified destination
        The user will be notified and no changes will be made.

        Parameters
        ----------
        passenger: str
            Username to be added to train's passenger set
        destination: str
            Train destination
        """

        self.lock.acquire()
        destination = destination.lower()
        res = ""
        if destination in self.trains:
            old_train = self.get_passenger_train(passenger)
            if old_train is not None and old_train.map_destination != destination:
                res = self.ditch_train(passenger, destination)
            train = self.trains[destination]
            err = train.add_passenger(passenger)
            self.lock.release()
            if err is not None:
                return err
            elif res == "":
                res = "%s jumped on the train to %s" % (passenger, train.display_destination)
                return res
            else:
                return res
        else:
            self.lock.release()
            return "That train doesn't exist, please try again or find a new train to join"

    def disembark_train(self, passenger, destination = None):
        # TODO: Allow users to board >1 train at a time
        """Remove a user from train passenger set

        If no more users remain on the specified train
        The train will be removed from the station

        Parameters
        ----------
        passenger: str
            User to be disembarked
        destination: str (optional)
            New train to be boarded
        """

        old_train = self.get_passenger_train(passenger)

        res = "%s disembarked from their train to %s" % (passenger, old_train.display_destination)
        if destination != None:
            res += "in favour of one to %s" % destination

        old_train.lock.acquire()
        old_train.passengers.remove(passenger)
        old_train.lock.release()

        if len(old_train.passengers) == 0:
            # TODO: Notify users that this train has been deleted
            self.delete_train(old_train.map_destination)

        return res

    def get_passenger_train(self, passenger):
        # TODO: Allow users to board >1 train at a time
        """Display the train the passenger has boarded

        Parameters
        ----------
        passenger: str
            User to be searched for among the trains
        """

        for dest in self.trains:
            train = self.trains[dest]
            if passenger in train.passengers:
                return train
        # TODO: Notify user if they are not on a train
        return None

    def StartTrainCommand(self, conductor, destination, time):
        self.Lock.acquire()
        res = ""
        oldTrain = self.GetPassengerTrain(conductor)
        if oldTrain is not None and oldTrain.MapDestination != destination:
            res = self.DitchTrain(conductor, destination)
        newTrain = Train(conductor, destination, time)
        err = self.AddTrain(newTrain)
        if err is not None:
            self.Lock.release()
            return err
        else:
            if res != "":
                res += "\n"
            res += "%s has started a train to %s that leaves in %d minutes!" % (conductor, newTrain.DisplayDestination, newTrain.TimeRemaining)
            if newTrain.TimeRemaining == 1:
                res = "%s has started a train to %s that leaves in %d minute!" % (conductor, newTrain.DisplayDestination, newTrain.TimeRemaining)
        self.Lock.release()
        worker = TrainWorker(self, newTrain)
        worker.start()
        return res


def GetTime(message):
    if IsInt(message[-1]):
        time = int(message[-1])
        if time <= 0:
            return None, "Please specify a time greater than 0 mins"
        return int(message[-1]), None
    else:
        return None, "Couldn't parse your time to departure. Please make sure it's an int >= 1"


def IsInt(val):
    try:
        int(val)
        return True
    except:
        return False


class TrainWorker(threading.Thread):
    def __init__(self, station, train):
        threading.Thread.__init__(self)
        self.Station = station
        self.Train = train
        # Implement a separate counter (in seconds) to refresh the station more "instantaneously"
        self.TimeRemaining = train.TimeRemaining * 60

    def run(self):
        while self.TimeRemaining >= 0:
            time.sleep(1)
            self.TimeRemaining -= 1
            if len(self.Train.Passengers) == 0 or self.Train.MapDestination not in self.Station.Trains:
                return
            message = ""
            if self.TimeRemaining == 60:
                message = "Reminder, the next train to %s leaves in one minute" % self.Train.DisplayDestination
            elif self.TimeRemaining == 0:
                message = "The train to %s has left the station with %s on it!" % (self.Train.DisplayDestination, self.Train.PassengerString())
                self.Station.DeleteTrain(self.Train.MapDestination)
            if message != "":
                PostMessage(message)


def Handler(station, user, message):
    message = message.split(' ')
    command = message[0]
    message = message[1:]
    notFound = "Your train/destination could not be found, please try again"
    if command == "help":
        return station.HelpCommand()
    elif command == "active" and len(message) == 0:
        return station.ActiveTrainCommand()
    elif command == "join" and len(message) >= 1:
        if len(message) == 0:
            return notFound
        else:
            return station.JoinTrainCommand(user, ' '.join(message))
    elif command == "start" and len(message) >= 2:
        time, err = GetTime(message)
        destination = message[:-1]
        destination = ' '.join(destination)
        if err is not None:
            return err
        elif len(destination) == 0:
            return notFound
        else:
            return station.StartTrainCommand(user, destination, time)
    else:
        return "Your command could not be found or was malformed, please view the help message (/train help) for more details"


def PostMessage(message):
    webhook_url = 'fake url'
    slack_data = {'text': message, 'response_type': 'in_channel'}
    response = requests.post(webhook_url, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})
