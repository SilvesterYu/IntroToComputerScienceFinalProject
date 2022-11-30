"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""

import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp


class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices = {}
        # according to my interpretation
        # key: name, value: the chat history as an Index object
        # sonnet
        self.sonnet = indexer.PIndex("AllSonnets.txt")

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        # read the msg that should have login code plus username
        try:
            # receive msg from this socket
            msg = json.loads(myrecv(sock))
            if len(msg) > 0:
                # when the user of this socket wishes to log in
                if msg["action"] == "login":
                    name = msg["name"]
                    # if this user is NOT YET in the system
                    if self.group.is_member(name) != True:
                        # move socket from new clients list to logged clients
                        self.new_clients.remove(sock)
                        # add into the name to sock mapping
                        self.logged_name2sock[name] = sock
                        self.logged_sock2name[sock] = name
                        # load chat history of that user
                        # if this person has no chat history
                        if name not in self.indices.keys():
                            try:
                                # open the txt file corresponding to this user, and read
                                self.indices[name] = pkl.load(
                                    open(name + '.idx', 'rb')) # file created in this step
                            except IOError:  # chat index does not exist, then create one
                                self.indices[name] = indexer.Index(name)
                                # self.indices.keys()--my name.
                        # after all the arrangements above, this user is logged in
                        # has their socket and name in dictionary
                        # and has a corresponding dictionary to record their chat history
                        print(name + ' logged in')
                        # adding this person to the members{}, initial state == S_ALONE
                        self.group.join(name)
                        # send out a signal that this person successfully logged in, status: ok
                        mysend(sock, json.dumps(
                            {"action": "login", "status": "ok"}))
                    else:  # a client under this name has already logged in
                        # sends out a signal indicating duplicated logging in
                        mysend(sock, json.dumps(
                            {"action": "login", "status": "duplicate"}))
                        # print out this info to user, about the duplication.
                        print(name + ' duplicate login attempt')
                else:
                    # when there's sth wrong with 'if msg["action"] == "login"' statement
                    print('wrong code received')
            else:  # client died unexpectedly
                # no msg extracted from 'msg = json.loads(myrecv(sock))'
                self.logout(sock)
        except:
            self.all_sockets.remove(sock)
            # if sth goes wrong with the above, remove this socket from all_sockets []

    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        # dump the chat history of this socket in to corresponding txt file
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        # delete the chat history in this indices[name] value
        del self.indices[name]
        # remove both name and its socket from the dictionaries
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        # remove the socket itself from all_sockets []
        self.all_sockets.remove(sock)
        # remove the person from the group they are in
        self.group.leave(name)
        # close the socket????????????????????????
        sock.close()

# ==============================================================================
# main command switchboard
# ==============================================================================
    def handle_msg(self, from_sock):
        # read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
            # ==============================================================================
            # handle connect request this is implemented for you
            # ==============================================================================
            msg = json.loads(msg)

            #-------------------------connecting part-------------------------------
            if msg["action"] == "connect":
                # name of the person that this user wants to connect to
                to_name = msg["target"]
                # the name of this user themself
                from_name = self.logged_sock2name[from_sock]
                # if this user tries to connect to themself...hmmmm...hahaha
                if to_name == from_name:
                    msg = json.dumps({"action": "connect", "status": "self"})
                # connect to the peer
                # ok, this is the situation in which user is not so 皮 as to connect to themself.
                # so if this peer is a member in this system, 就好办了
                elif self.group.is_member(to_name):
                    # find the peer's socket
                    to_sock = self.logged_name2sock[to_name]
                    # in the group management, put these two people happily in a group (a list)
                    self.group.connect(from_name, to_name)
                    # stores the names of all people in "my" group
                    the_guys = self.group.list_me(from_name)
                    # sends out a signal indicating my successful connection!!
                    msg = json.dumps(
                        {"action": "connect", "status": "success"})
                    # iterate through all the members other than myself.
                    for g in the_guys[1:]:
                        # extract every one of their sockets
                        to_sock = self.logged_name2sock[g]
                        # send a signal to them, informing them of my arrival.

                        mysend(to_sock, json.dumps(
                            {"action": "connect", "status": "request", "from": from_name}))
                else:
                    # if this peer is NOT a member of this system...
                    # send a signal regarding the "no-user" problem
                    msg = json.dumps(
                        {"action": "connect", "status": "no-user"})
                # sends back the info collected, to me.
                # fine.
                mysend(from_sock, msg)
                #---------------------------end of connecting part----------------------------

# ==============================================================================
# handle messeage exchange: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "exchange":
                # extract my name.
                from_name = self.logged_sock2name[from_sock]
                """
                Finding the list of people to send to and index message
                """
                # IMPLEMENTATION
                # ---- start your code ---- #
                message = msg["message"]
                if from_name not in self.indices.keys():
                    self.indices[from_name] = indexer.Index(from_name)
                    self.indices[from_name].add_msg_and_index(message)
                else:
                    self.indices[from_name].add_msg_and_index(message)
                # ---- end of your code --- #

                the_guys = self.group.list_me(from_name)[1:]
                for g in the_guys:
                    to_sock = self.logged_name2sock[g]

                    # IMPLEMENTATION
                    # ---- start your code ---- #

                    message2 = {"action": "exchange", "from": "[" + from_name + "]", "message": message}
                    mysend(
                        to_sock, message2)

                    # ---- end of your code --- #

# ==============================================================================
# the "from" guy has had enough (talking to "to")!
# ==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps(
                        {"action": "disconnect", "msg": "everyone left, you are alone"}))
# ==============================================================================
#                 listing available peers: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "list":

                # IMPLEMENTATION
                # ---- start your code ---- #

                available = []
                for person in self.group.members.keys():
                    available.append(person)

                msg = ','.join(available)

                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "list", "results": msg}))
# ==============================================================================
#             retrieve a sonnet : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "poem":

                # IMPLEMENTATION
                # ---- start your code ---- #

                poem_idx = msg["target"]
                sentence_list = self.sonnet.get_poem(poem_idx)
                poem = "\n".join(sentence_list)
                print('here:\n', poem)

                # ---- end of your code --- #

                mysend(from_sock, json.dumps(
                    {"action": "poem", "results": poem}))
# ==============================================================================
#                 time
# ==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps(
                    {"action": "time", "results": ctime}))
# ==============================================================================
#                 search: : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "search":

                # IMPLEMENTATION
                # ---- start your code ---- #

                result_dict = {}
                # key: owner of the message sent
                # value: the actual sentence containing the term
                result_list = [] # a list storing the result
                term = msg["target"]
                for a_name in self.indices.keys():
                    # search for the lines containing this term in everyone's chat history
                    a_result = self.indices[a_name].search(term)
                    result_dict[a_name] = a_result
                for key, value in result_dict.items():
                    line = key + ": " + value # who said what
                    result_list.append(line)
                search_rslt = "\n".join(result_list)
                print("server side search: " + search_rslt)

                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "search", "results": search_rslt}))

# ==============================================================================
#                 the "from" guy really, really has had enough
# ==============================================================================

        else:
            # client died unexpectedly
            self.logout(from_sock)

# ==============================================================================
# main loop, loops *forever*
# ==============================================================================
    def run(self):
        print('starting server...')
        while(1):
            read, write, error = select.select(self.all_sockets, [], [])
            print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)


def main():
    server = Server()
    server.run()


if __name__ == '__main__':
    main()


