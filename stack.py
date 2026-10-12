class HistoryStack:

    def __init__(self):
        self.stack = []

    def push(self, transaction):
        """Add transaction to stack."""
        self.stack.append(transaction)

    def pop(self):
        """Remove latest transaction."""
        if self.is_empty():
            return None

        return self.stack.pop()

    def peek(self):
        """Return latest transaction without removing."""
        if self.is_empty():
            return None

        return self.stack[-1]

    def is_empty(self):
        return len(self.stack) == 0

    def size(self):
        return len(self.stack)

    def get_history(self):
        return self.stack[::-1]


# Example
if __name__ == "__main__":

    history = HistoryStack()

    history.push("Book Issued")
    history.push("Book Returned")
    history.push("Book Issued Again")

    print("Latest:", history.peek())

    print("History:")
    print(history.get_history())