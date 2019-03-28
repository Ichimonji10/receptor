class Router:
    def forward(self, outer_envelope, next_hop):
        """
        Forward a message on to the next hop closer to its destination
        """
        raise NotImplementedError()
    
    def next_hop(self, recipient):
        """
        Return the node ID of the next hop for routing a message to the
        given recipient. If the current node is the recipient, then return
        None.
        """
        raise NotImplementedError()
    
    def send(self, outer_envelope):
        """
        Send a new message with the given outer envelope.
        """
        raise NotImplementedError()
        