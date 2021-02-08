class Network():
    def __init__(self):
        pass

    def Transmit(self):
        pass

    def Receive(self):
        pass

class ZMQNetwork(Network):
    import zmq
    def __init__(self,id,controllerAddress,requestPortNumber,pubPortNumber):
        self.context = self.zmq.Context()
        self.id      = id
        self.sockclient = self.context.socket(self.zmq.REQ)
        self.socksub    = self.context.socket(self.zmq.SUB) 
        self.sockclient.connect('tcp://'+controllerAddress+':'+str(requestPortNumber))
        self.socksub.connect('tcp://'+controllerAddress+':'+str(pubPortNumber))
        self.socksub.setsockopt(self.zmq.SUBSCRIBE,b'')

    def Transmit(self,messages):
        n = len(messages)
        for i,msg in enumerate(messages):
            self.sockclient.send_json({'type':'report','count':(n-1)-i,'payload':msg})
            request = self.sockclient.recv_json() 

        messages = []

    def Synchronize(self):
        synchronized = False
        while not synchronized:
            print('waiting for publisher message')
            message = self.socksub.recv_json()
            if message['type'] == 'sync_req':
                synchronized = True
            self.sockclient.send_json({'type':'sync_rep','status':synchronized})
            self.sockclient.recv_json()


    def Receive(self):
        messages = []
        complete = False
        while not complete:
            message = self.socksub.recv_json()
            if message['type'] == 'telemetry':
                messages.append(message['payload'])
            elif message['type'] == 'run':
                complete = True

        return messages

class Controller:
    import zmq;
    def __init__(self,numSubs,serverPort,pubPort):
        self.ctx = self.zmq.Context() 
        self.sockserver = self.ctx.socket(self.zmq.REP)
        self.sockpub    = self.ctx.socket(self.zmq.PUB)
        self.sockpub.bind('tcp://*:'+str(pubPort))
        self.sockserver.bind('tcp://*:'+str(serverPort))
        self.numSubs   = numSubs
        self.poller = self.zmq.Poller()
        self.poller.register(self.sockserver, self.zmq.POLLIN)
        self.timeout = 1500

    def Run(self):

        print('Starting runner')
        subs = 0

        # Synchronize all subscribers
        while subs < self.numSubs:
            print('waiting for subscribers:',self.numSubs - subs)
            self.sockpub.send_json({'type':'sync_req'})
            socks = dict(self.poller.poll(self.timeout))
            if socks.get(self.sockserver) == self.zmq.POLLIN:
                msg = self.sockserver.recv_json()
                self.sockserver.send_json({})
                if msg['type'] == 'sync_rep':
                    if msg['status']:
                        subs = subs + 1
                        print('Found subscriber...')

        print('All subscribers synchronized')

        # Trigger the first step in all simulations
        self.sockpub.send_json({'type':'run'})
        count = 0
        while True:
            # Listen for reports from clients
            socks = dict(self.poller.poll(self.timeout))
            if socks.get(self.sockserver) == self.zmq.POLLIN:
                msg = self.sockserver.recv_json()
                if msg['type'] == 'report':
                    #print(msg['count'],msg['payload'])
                    # If report is multipart, requests parts
                    if msg['count'] != 0:
                        #print('sending report')
                        self.sockserver.send_json({'type':'send_report'})
                    else:
                        # Acknowledge final receipt
                        #print('sending ack')
                        self.sockserver.send_json({'type':'received'})
                        count = count + 1

                # Send telemtry to all subscribers
                #print('send to all subs')
                self.sockpub.send_json({'type':'telemetry','payload':msg['payload']})

                # Trigger to run simulation step
                if count == self.numSubs:
                    #print('send runs')
                    self.sockpub.send_json({'type':'run'})
                    count = 0

if __name__ == '__main__':
    controller = Controller(2,14550,14551)
    controller.Run()
