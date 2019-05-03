from perfectpointtopointlinks import PerfectPointToPointLinks


class BestEffortBroadcast:

    def __init__(self, process_id, addr_str, callback, arg_callback):
        self.address = addr_str
        self.deliver_call_back = callback
        self.arg_callback = arg_callback
        self.links = PerfectPointToPointLinks(port=process_id, addr_str=addr_str, arg_callback=self.deliver)

    def close(self):
        self.links.close()

    def deliver(self, sender_id, message):
        if message is not None:
            self.deliver_call_back((sender_id, message), self.arg_callback)

    def broadcast(self, message, process_id_list):
        for process_id in process_id_list:
            self.links.send(process_id, self.address, message)
