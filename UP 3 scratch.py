"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json


class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        # compose a msg to server, containing "action" and "target"
        msg = json.dumps({"action": "connect", "target": peer})
        # sends it to server
        mysend(self.s, msg)
        # load the response that this socket receives form the server
        response = json.loads(myrecv(self.s))
        # if the server tells this socket that the connection was successful
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with ' + self.peer + '\n'
            #--------------------return value here--------------------
            # only if successful can it return true
            return (True)
        # if the server returns info that the target user is busy
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        # if the server detects that this socket attemps to connect to itself...
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        # if the server detects that the target user isn't in the system
        else:
            self.out_msg += 'User is not online, try again later\n'
        #-------------otherwise return false--------------------
        return (False)

    def disconnect(self):
        # compose a msg to server, containing "action" to disconnect
        msg = json.dumps({"action": "disconnect"})
        # send this msg
        mysend(self.s, msg)
        # this appears on my screen
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        # my_msg: the thing I type in
        # peer_msg: the encoded message this socket receives from server

        # initialize the line that is to appear on my screen
        self.out_msg = ''
        # ==============================================================================
        # Once logged in, do a few things: get peer listing, connect, search
        # And, of course, if you are so bored, just go
        # This is event handling instate "S_LOGGEDIN"
        # ==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            #----------------------------things I type in-------------------------------
            if len(my_msg) > 0:

                # If I type in "q", will appear on my screen the info that I quited
                # my state becomes S_OFFLINE
                # so my actions no longer gets processed under this "if" statement
                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                # If I type in "time"
                # sends a msg to the server about my request for the time
                # receives the server's msg back to me which contains time,
                # and it gets printed on my screen
                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action": "time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                # If I request to know who the fck are in this system
                # sends a msg to the server about my request
                # loads the server's search results that are sent back to me
                # adds this to the message that's to be printed on my screen ultimately
                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action": "list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                # If I request to connect to a peer
                # extract the name of this peer from the thing I typed in
                # use the connect_to() function here to check if the connection is valid
                # if valid, my state becomes S_CHATTING, no longer under this "if" statement
                # prints out a message to me regarding my successful connection with this peer

                # if not successful, don't change anything
                # just prints out a message to me regarding the unsuccessful connection
                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                # If I request to search for a term in the chat history
                # extract the term I wish to search for, from the thing I typed in
                # sends a msg to the server about my request to search for chat history
                # receives the search result that the server sends back to me
                # if there is any, print it on my screen. If not, print "not found" on my screen
                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action": "search", "target": term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                # if I request to receive a poem from the server
                # extract the poem index from the thing I typed in
                # sends a msg to the server regarding my request for this specific poem
                # receives the result the servers sends back to me
                # if there is any, print poem on my screen, if not, print "not found" on my screen
                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action": "poem", "target": poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                # if the thing I typed in was according to the protocol, satisfies non of the above
                # prints the menu on my screen to tell me the protocol
                else:
                    self.out_msg += menu

            #--------------------------things peer types in--(me: S_LOGGENIN)---------------------------------
            # the peer_msg is something this state machine receives from the server
            # regarding the actions done by peer
            # therefore it can turn into a dictionary via json.load()
            if len(peer_msg) > 0:
                try:
                    peer_msg = json.loads(peer_msg)
                except Exception as err:
                    self.out_msg += " json.loads failed " + str(err)
                    return self.out_msg

                # If this peer tries to connect, and is valid.
                # on the server side, this peer just gets put into the target group
                if peer_msg["action"] == "connect":
                    # ----------your code here------#

                    print(peer_msg)
                    self.out_msg = peer_msg["from"] + " joins this group! Greet your new peer!"

                    # ----------end of your code----#

        # ==============================================================================
        # Start chatting, 'bye' for quit
        # This is event handling instate "S_CHATTING"
        # ==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:  # my stuff going out
                mysend(self.s, json.dumps({"action": "exchange", "from": "[" + self.me + "]", "message": my_msg}))
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:  # peer's stuff, coming in

                # ----------your code here------#
                peer_msg = json.loads(peer_msg)

                if peer_msg["action"] == "exchange":
                    print(peer_msg)
                    peer_name = peer_msg["from"]
                    peer_message = peer_msg["message"]
                    self.out_msg = peer_name + ":" + peer_message

                if peer_msg["action"] == "disconnect":
                    # the situation where the peer disconnects and server sends me a message
                    # this happens when I'm the only one left
                    inform = peer_msg["msg"]
                    self.out_msg = inform

                # ----------end of your code----#

            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
        # ==============================================================================
        # invalid state
        # ==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        # def proc()'s ultimate purpose is to print out out_msg lines on my screen.
        return self.out_msg
