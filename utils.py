async def process_stream(stream, add_message=None):
    """
    Stream messages and update conversation in real-time.

    Parameters:
        stream (async generator): The stream of messages.
        add_message (function, optional): A callback function to handle the resolution of a new message.
                                          Defaults to printing the message.
    """
    conversation = []  # Initialize an empty list to store the conversation as dictionaries

    def console_print_message(message):
        if isinstance(message, tuple):
            print(message)  # Print the tuple message
        else:
            message.pretty_print()  # Pretty print other message types

    # Process the stream
    async for s in stream:
        message = s["messages"][-1]  # Get the last message
        console_print_message(message)
        if add_message:
            add_message(message)
        conversation.append(message)  # Store the message in the conversation list
    return conversation  # Return the entire conversation


def print_answer(stream):
    s = list(stream)[-1]
    message = s["messages"][-1]
    if isinstance(message, tuple):
        print(message)
    else:
        message.pretty_print()
