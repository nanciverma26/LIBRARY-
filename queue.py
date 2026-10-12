from collections import deque


class WaitingQueue:

    def __init__(self):
        self.queue = deque()

    def enqueue(self, user_id):
        """Add user to the rear of queue."""
        self.queue.append(user_id)

    def dequeue(self):
        """Remove and return first user."""
        if self.is_empty():
            return None

        return self.queue.popleft()

    def front(self):
        """Return first user without removing."""
        if self.is_empty():
            return None

        return self.queue[0]

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)

    def get_queue(self):
        return list(self.queue)


# Example
if __name__ == "__main__":

    waiting = WaitingQueue()

    waiting.enqueue(1)
    waiting.enqueue(2)
    waiting.enqueue(3)

    print("Waiting Queue:", waiting.get_queue())

    print("Next user:", waiting.dequeue())

    print("Remaining Queue:", waiting.get_queue())