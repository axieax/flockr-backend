''' Test file for message.py '''
from time import sleep
from datetime import datetime
import pytest
from auth import auth_register
from channel import channel_messages, channel_invite
from channels import channels_create
from message import (
    message_send, message_remove, message_edit, message_sendlater,
    message_react, message_unreact, message_pin, message_unpin,
)
from error import InputError, AccessError
from other import clear

def test_message_send_invalid():
    '''
    Test:
        - Sending message with invalid token
        - Sending message with invalid channel id
        - Sending message without being a member of channel
        - Sending empty messages
        - Sending messages that are too long (1000+ characters)

    Scenario:
        - Owner registers and creates channel
        - Test tries to send message with invalid token
        - Owner tries to send message in an invalid channel
        - random_user registers and creates channel
        - Owner tries to send message in random_user's channel without being a member
        - random_user tries to send message in owner's channel without being a member
        - Owner tries to send an empty string and a 1001 character string
    '''

    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Boss')
    f_channel = channels_create(f_owner['token'], 'Main Channel', True)

    # Invalid token
    with pytest.raises(AccessError):
        message_send('', f_channel['channel_id'], 'Test Message')
    # Invalid channel
    with pytest.raises(InputError):
        message_send(f_owner['token'], f_channel['channel_id'] + 100, 'Test message')

    random_user = auth_register('random@gmail.com', 'password', 'Random', 'User')
    r_channel = channels_create(random_user['token'], 'Random Channel', True)

    # User not in channel as member
    with pytest.raises(AccessError):
        message_send(f_owner['token'], r_channel['channel_id'], 'f_owner in r_channel')
    with pytest.raises(AccessError):
        message_send(random_user['token'], f_channel['channel_id'], 'random_user in f_channel')

    # Message lengths
    with pytest.raises(InputError):
        message_send(f_owner['token'], f_channel['channel_id'], '')
    message = 'A' * 1001
    with pytest.raises(InputError):
        message_send(f_owner['token'], f_channel['channel_id'], message)
    with pytest.raises(InputError):
        message_send(f_owner['token'], f_channel['channel_id'], message + 'x')


def test_message_send_valid():
    '''
    Test:
        - Sending messages normally

    Scenario:
        - Owner registers and creates channel
        - random_user registers
        - Owner invites random_user and random_user joins owner's channel
        - Owner sends message
        - Test checks that message was sent
        - Owner and user send multiple messages of increasing lengths
    '''
    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Boss')
    f_channel = channels_create(f_owner['token'], 'Main Channel', True)
    random_user = auth_register('random@gmail.com', 'password', 'Random', 'User')
    channel_invite(f_owner['token'], f_channel['channel_id'], random_user['u_id'])

    # Message lengths
    message_send(f_owner['token'], f_channel['channel_id'], 'First message')
    output = channel_messages(f_owner['token'], f_channel['channel_id'], 0)
    assert len(output['messages']) == 1

    message = 'A'
    for multiple in range(1, 1001):
        message_send(f_owner['token'], f_channel['channel_id'], multiple * message)
        message_send(random_user['token'], f_channel['channel_id'], multiple * message)


def test_message_remove():
    '''
    Test:
        - Removing message with invalid message id
        - Removing message with invalid token
        - Removing message without being owner of channel or message
        - Removing message whilst being owner of message or channel
        - Removing already removed message

    Scenario:
        - Owner registers and creates channel
        - random_user and random_user2 join owner's channel
        - Owner sends message
        - Owner tries to remove invalid message
        - Both users send messages
        - Test tries to remove first message with invalid token
        - Users try to remove owner's message (should not work)
        - random_user2 removes their own message
        - Owner removes random_user's message
        - Owner removes it's own message
        - Owner tries to remove removed message
    '''
    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Boss')
    f_channel = channels_create(f_owner['token'], 'Main Channel', True)
    random_user = auth_register('random@gmail.com', 'password', 'Random', 'User')
    channel_invite(f_owner['token'], f_channel['channel_id'], random_user['u_id'])
    random_user2 = auth_register('randomguy@gmail.com', 'password', 'Random2', 'Guy2')
    channel_invite(f_owner['token'], f_channel['channel_id'], random_user2['u_id'])

    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'First msg')['message_id']

    # Invalid message_id
    with pytest.raises(InputError):
        message_remove(f_owner['token'], m_id1 + 1)

    m_id2 = message_send(random_user['token'], f_channel['channel_id'], 'Second msg')['message_id']
    m_id3 = message_send(random_user2['token'], f_channel['channel_id'], 'Third msg')['message_id']

    # Invalid token
    with pytest.raises(AccessError):
        message_remove('', m_id1)

    # Authorised user did not send the message and is not channel or Flockr owner
    with pytest.raises(AccessError):
        message_remove(random_user['token'], m_id1)
    with pytest.raises(AccessError):
        message_remove(random_user2['token'], m_id2)

    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']
    assert len(messages) == 3

    # Message sender can remove their own message
    message_remove(random_user2['token'], m_id3)
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']
    assert len(messages) == 2

    # Flockr owner can remove anyone's message
    message_remove(f_owner['token'], m_id2)
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']
    assert len(messages) == 1

    # Flockr owner can remove their own message
    message_remove(f_owner['token'], m_id1)
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']
    assert len(messages) == 0

    # Message_id no longer exists
    with pytest.raises(InputError):
        message_remove(f_owner['token'], m_id1)


def test_message_edit():
    '''
    Test:
        - Editing message with invalid message id
        - Editing message with invalid token
        - Editing message without being owner of channel or message
        - Editing message whilst being owner of message or channel
        - Editing message to an empty string for deletion

    Scenario:
        - Owner registers and creates channel
        - random_user and random_user2 join owner's channel
        - Owner sends message
        - Owner tries to edit first message with invalid message id
        - Users both send messages
        - Test tries to edit first message with invalid token
        - Users try to edit messages without being owner of channel or message
        - Users edit their own messages
        - Owner edits user's messages
        - Users try to delete messages via editing without being owner of channel or message
        - Owner deletes user's messages via edit to empty string
    '''

    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Boss')
    f_channel = channels_create(f_owner['token'], 'Main Channel', True)
    random_user = auth_register('random@gmail.com', 'password', 'Random', 'User')
    channel_invite(f_owner['token'], f_channel['channel_id'], random_user['u_id'])
    random_user2 = auth_register('randomguy@gmail.com', 'password', 'Random2', 'Guy2')
    channel_invite(f_owner['token'], f_channel['channel_id'], random_user2['u_id'])

    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'First msg')['message_id']

    # Invalid message_id
    with pytest.raises(InputError):
        message_edit(f_owner['token'], m_id1 + 1, 'Edited first message')

    m_id2 = message_send(random_user['token'], f_channel['channel_id'], 'Second msg')['message_id']
    m_id3 = message_send(random_user2['token'], f_channel['channel_id'], 'Third msg')['message_id']

    # Invalid token
    with pytest.raises(AccessError):
        message_edit('', m_id1, 'Edited first message')

    # Check messages content
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']
    messages = [message['message'] for message in messages]
    assert messages == ['Third msg', 'Second msg', 'First msg']

    # Authorised user did not send the message and is not channel or Flockr owner
    with pytest.raises(AccessError):
        message_edit(random_user['token'], m_id1, 'Edited first message')
    with pytest.raises(AccessError):
        message_edit(random_user2['token'], m_id2, 'Edited second message')

    # Message sender can edit their own message
    message_edit(random_user2['token'], m_id3, 'Edited third message')

    # Flockr owner can edit anyone's message
    message_edit(f_owner['token'], m_id2, 'Edited second message')

    # Flockr owner can edit their own message
    message_edit(f_owner['token'], m_id1, 'Edited first message')

    # Check messages content
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']
    messages = [message['message'] for message in messages]
    assert messages == ['Edited third message', 'Edited second message', 'Edited first message']

    # If the edited message becomes an empty string, it should be deleted
    m_id4 = message_send(f_owner['token'], f_channel['channel_id'], 'Fourth msg')['message_id']
    m_id5 = message_send(random_user['token'], f_channel['channel_id'], 'Fifth msg')['message_id']
    m_id6 = message_send(random_user2['token'], f_channel['channel_id'], 'Sixth msg')['message_id']

    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']
    assert len(messages) == 6

    # Authorised user did not send the message is not channel or Flockr owner
    with pytest.raises(AccessError):
        message_edit(random_user['token'], m_id4, '')
    with pytest.raises(AccessError):
        message_edit(random_user2['token'], m_id5, '')

    # Message sender can delete their own message by editing it to an empty message
    message_edit(random_user2['token'], m_id6, '')

    # Flockr owner can delete anyone's message by editing it to an empty message
    message_edit(f_owner['token'], m_id5, '')

    # Flockr owner can delete their own message by editing it to an empty message
    message_edit(f_owner['token'], m_id4, '')

    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']
    assert len(messages) == 3


def test_message_sendlater_invalid():
    '''
    Test:
        - Sending a message later with an invalid token
        - Sending a message later with an invalid channel id
        - Sending a message later without being a member of channel
        - Sending a message later with an invalid length

    Scenario:
        - Owner registers and creates channel
        - Owner tries to send message later with invalid time
        - Owner tries to send message later with invalid token
        - Owner tries to send message later with invalid channel id
        - Random user registers and tries to send later without being member of channel
    '''
    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Boss')
    f_channel = channels_create(f_owner['token'], 'Main Channel', True)

    time_sent = datetime.timestamp(datetime.now()) - 2

    # Time is in the past
    with pytest.raises(InputError):
        message_sendlater(f_owner['token'], f_channel['channel_id'], 'Test message', time_sent)

    time_sent = datetime.timestamp(datetime.now()) + 2

    # Invalid token
    with pytest.raises(AccessError):
        message_sendlater('', f_channel['channel_id'], 'Test Message', time_sent)

    # Invalid channel
    with pytest.raises(InputError):
        message_sendlater(f_owner['token'], f_channel['channel_id'] + 100, 'Test msg', time_sent)

    random_user = auth_register('random@gmail.com', 'password', 'Random', 'User')
    r_channel = channels_create(random_user['token'], 'Random Channel', True)

    # User not in channel as member
    with pytest.raises(AccessError):
        message_sendlater(
            f_owner['token'], r_channel['channel_id'], 'f_owner in r_channel', time_sent
        )
    with pytest.raises(AccessError):
        message_sendlater(
            random_user['token'], f_channel['channel_id'], 'random_user in f_channel', time_sent
        )

    # Message lengths
    with pytest.raises(InputError):
        message_sendlater(f_owner['token'], f_channel['channel_id'], '', time_sent)
    message = 'A' * 1001
    with pytest.raises(InputError):
        message_sendlater(f_owner['token'], f_channel['channel_id'], message, time_sent)
    with pytest.raises(InputError):
        message_sendlater(f_owner['token'], f_channel['channel_id'], message + 'x', time_sent)


def test_message_sendlater_valid():
    '''
    Test:
        - Testing valid use of sending a message later

    Scenario:
        - Owner registers and creates channel
        - Owner sends a message later
        - Test checks that message is sent
    '''
    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Boss')
    f_channel = channels_create(f_owner['token'], 'Main Channel', True)

    time_sent = datetime.timestamp(datetime.now()) + 2

    # Message lengths
    message_sendlater(f_owner['token'], f_channel['channel_id'], 'First message', time_sent)
    output = channel_messages(f_owner['token'], f_channel['channel_id'], 0)
    assert len(output['messages']) == 0

    sleep(3)
    output = channel_messages(f_owner['token'], f_channel['channel_id'], 0)
    assert len(output['messages']) == 1


def test_message_react_valid():
    '''
    Test:
        - Multiple users reacting to the same message

    Scenario:
        - Owner registers and creates channel
        - Random users register and join owner's channel
        - Owner sends message
        - random_user reacts to the message
        - Test checks that only 1 random user has reacted
        - From the owner's point of view, it shows that the owner has not reacted
        - random_user2 has reacted to the same message
        - Test checks that the message has been reacted to by both random users
        - From the random_user point of view, it shows that random_user has reacted to the msg
    '''
    clear()

    # Making a normal channel
    f_owner = auth_register('fox@gmail.com', 'password', 'Fox', 'Foxson')
    f_channel = channels_create(f_owner['token'], 'Main HUB', True)

    # Invite a random user to the channel
    random_user = auth_register('random@gmail.com', 'password', 'Random', 'User')
    channel_invite(f_owner['token'], f_channel['channel_id'], random_user['u_id'])

    # Invite a second user
    random_user2 = auth_register('randomguy@gmail.com', 'password', 'Random2', 'Guy2')
    channel_invite(f_owner['token'], f_channel['channel_id'], random_user2['u_id'])

    # Owner sends message
    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'I came first!')['message_id']

    # Random user reacts to the message (the given react_id is 1)
    message_react(random_user['token'], m_id1, 1)

    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check if the user has reacted and check if the owner itself has reacted
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['reacts'][0]['react_id'] == 1
            assert message['reacts'][0]['u_ids'] == [random_user['u_id']]
            assert message['reacts'][0]['is_this_user_reacted'] is False

    # Second user reacts to the same message
    message_react(random_user2['token'], m_id1, 1)

    # Check if another user has reacted and check if a random user itself has reacted
    messages = channel_messages(random_user['token'], f_channel['channel_id'], 0)['messages']

    for message in messages:
        if message['message_id'] == m_id1:
            assert message['reacts'][0]['react_id'] == 1
            assert message['reacts'][0]['u_ids'] == [random_user['u_id'], random_user2['u_id']]
            assert message['reacts'][0]['is_this_user_reacted']


def test_message_react_invalid():
    '''
    Test:
        - User react with invalid tokens
        - User react with invalid message id
        - User react with invalid react id

    Scenario:
        - The owner registers an account and creates a channel
        - The user creates an account and gets invited to the channel
        - The owner sends a message
        - Invalid user tries to react to the message
        - Valid user tries to react to non existent message
        - Valid user tries to react with invalid react id
    '''
    clear()

    # Register an owner, create channel and invite user
    # Owner sends message
    owner = auth_register('wolf@gmail.com', 'password', 'wolf', 'wolfson')
    channel = channels_create(owner['token'], 'Main HUB', True)
    user = auth_register('random@gmail.com', 'password', 'User', 'Userson')
    channel_invite(owner['token'], channel['channel_id'], user['u_id'])
    m_id1 = message_send(owner['token'], channel['channel_id'], 'I was here!')['message_id']

    # Invalid user
    with pytest.raises(AccessError):
        message_react('@#($*&', m_id1, 1)

    # Invalid message id
    with pytest.raises(AccessError):
        message_react(user['token'], m_id1 + 1000, 1)

    # Invalid react id
    with pytest.raises(InputError):
        message_react(user['token'], m_id1, 999)


def test_message_unreact_valid():
    '''
    Test:
        - Unreact the message after giving reaction

    Scenario:
        - Owner, user1 and user2 all create an account
        - The owner creates a channel and invites user1 and user2
        - The owner sends a message and all 3 users react to the message
        - Test that the message has gotten reactions from those 3 users
        - user1 and user2 unreact to the message
        - Test that the message has gotten reactions only from the owner
        - Owner unreacst the message
        - Test that the message has no reactions
    '''
    clear()

    owner = auth_register('wolf@gmail.com', 'password', 'wolf', 'wolfson')
    channel = channels_create(owner['token'], 'UNSW HUB', True)
    user = auth_register('random@gmail.com', 'password', 'User', 'Userson')
    user2 = auth_register('random2@gmail.com', 'password', 'User2', 'Userson2')
    channel_invite(owner['token'], channel['channel_id'], user['u_id'])
    m_id1 = message_send(owner['token'], channel['channel_id'], 'made you look!')['message_id']

    # 3 users reacted
    message_react(user['token'], m_id1, 1)
    message_react(user2['token'], m_id1, 1)
    message_react(owner['token'], m_id1, 1)

    messages = channel_messages(owner['token'], channel['channel_id'], 0)['messages']

    for message in messages:
        if message['message_id'] == m_id1:
            assert message['reacts'][0]['u_ids'] == [user['u_id'], user2['u_id'], owner['u_id']]

    # 2 users unreact
    message_unreact(user['token'], m_id1, 1)
    message_unreact(user2['token'], m_id1, 1)
    messages = channel_messages(owner['token'], channel['channel_id'], 0)['messages']

    for message in messages:
        if message['message_id'] == m_id1:
            assert message['reacts'][0]['u_ids'] == [owner['u_id']]

    # Another user unreacts
    message_unreact(owner['token'], m_id1, 1)
    messages = channel_messages(owner['token'], channel['channel_id'], 0)['messages']

    for message in messages:
        if message['message_id'] == m_id1:
            assert message['reacts'][0]['u_ids'] == []


def test_message_unreact_invalid():
    '''
    Test:
        - Invalid user tries to unreact the message
        - Valid user tries to unreact with invalid message id
        - Valid user tries to unreact with invalid react id

    Scenario:
        - The owner creates an account and a channel
        - The user creats an account and gets invited to the channel
        - The owner sends a message and the user reacts to it
        - Test that the invalid user tries to unreact to the message
        - Test that the valid user tries to unreact with invalid message id
        - Test that the valid user tries to unreact with invalid id
    '''
    clear()

    owner = auth_register('wolf@gmail.com', 'password', 'wolf', 'wolfson')
    channel = channels_create(owner['token'], 'UNSW HUB', True)
    user = auth_register('random@gmail.com', 'password', 'User', 'Userson')
    channel_invite(owner['token'], channel['channel_id'], user['u_id'])
    msg = 'please unreact this!'
    m_id1 = message_send(owner['token'], channel['channel_id'], msg)['message_id']

    # React
    message_react(user['token'], m_id1, 1)

    # Invalid user
    with pytest.raises(AccessError):
        message_unreact('@#($*&', m_id1, 1)

    # Invalid message id
    with pytest.raises(AccessError):
        message_unreact(user['token'], m_id1 + 666, 1)

    # Invalid react id
    with pytest.raises(InputError):
        message_unreact(user['token'], m_id1, 999)


def test_message_unreact_already_unreacted():
    '''
    Test:
        - Unreact on a message that contains no reacts at all

    Scenario:
        - The owner creates an account and channel
        - The user creats an account and gets invited to the channel
        - The owner sends a message
        - No one has reacted to the message at all
        - Test that the user tries to unreact with valid tokens, message id and react id
    '''
    clear()

    owner = auth_register('space@gmail.com', 'password', 'Einstein', 'Einsteinson')
    channel = channels_create(owner['token'], 'UNSW HUB', True)
    user = auth_register('zeke999@gmail.com', 'password', 'Zeke', 'Zekeson')
    channel_invite(owner['token'], channel['channel_id'], user['u_id'])
    msg = 'this message has no reaction'

    # There is an existing message
    m_id1 = message_send(owner['token'], channel['channel_id'], msg)['message_id']

    # Unreact to message that has no reacts
    with pytest.raises(InputError):
        message_unreact(user['token'], m_id1, 1)


def test_message_unreact_others_react():
    '''
    Test:
        - Unreact other user's reaction

    Scenario:
        - The owner, user1 and user2 creates an account
        - The owner creates a channel and invites user1 and user2
        - The owner sends the message
        - User1 reacts to the message while user2 does nothing at all
        - Check that the message has react only from user1
        - Test that the user2 unreact to the message that has react from user1
    '''
    clear()

    owner = auth_register('music@gmail.com', 'password', 'ipod', 'ipodson')
    channel = channels_create(owner['token'], 'UNSW HUB', True)
    # Create 2 users that will join the same channel
    user1 = auth_register('scary@gmail.com', 'password', 'Stranger', 'Danger')
    user2 = auth_register('creepy@gmail.com', 'password', 'Danger', 'Dangerson')
    channel_invite(owner['token'], channel['channel_id'], user1['u_id'])
    channel_invite(owner['token'], channel['channel_id'], user2['u_id'])
    msg = 'The quick brown fox jumps over the lazy dog'

    # Owner sends the message
    m_id1 = message_send(owner['token'], channel['channel_id'], msg)['message_id']

    # user1 reacts while user2 does nothing
    message_react(user1['token'], m_id1, 1)
    messages = channel_messages(owner['token'], channel['channel_id'], 0)['messages']

    # confirm user reacts
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['reacts'][0]['u_ids'] == [user1['u_id']]

    # user2 tries to unreact the message that user1 has reacted to
    with pytest.raises(AccessError):
        message_unreact(user2['token'], m_id1, 1)


def test_message_pin_valid():
    '''
    Test:
        - Pinning a message normally

    Scenario:
        - Two users register (owner and user)
        - Owner creates a private channel and invites user
        - Owner and user send messages
        - Test checks that all messages are not pinned
        - Owner pins 1 message
        - Test checks that the message is pinned
    '''
    clear()

    # Owner and User register
    f_owner = auth_register('johnmonkeyson@gmail.com', 'bananayummy', 'John', 'Monkeyson')
    f_user = auth_register('stevenson@gmail.com', 'ihatebananas', 'Steven', 'Stevenson')

    # Owner creates private channel
    f_channel = channels_create(f_owner['token'], 'Private Channel', False)

    # Owner invites f_user to channel
    channel_invite(f_owner['token'], f_channel['channel_id'], f_user['u_id'])

    # Owner and user send messages in f_channel (Private Channel)
    message_send(f_owner['token'], f_channel['channel_id'], 'hELLO wOORLD!')
    message_send(f_owner['token'], f_channel['channel_id'], 'hello?')

    m_id3 = message_send(f_user['token'], f_channel['channel_id'], 'pin this pls')['message_id']

    message_send(f_owner['token'], f_channel['channel_id'], 'bye world')

    # Get messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that all messages are not pinned
    for message in messages:
        assert message['is_pinned'] is False

    # Owner pins a message
    message_pin(f_owner['token'], m_id3)

    # Update messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is pinned
    for message in messages:
        if message['message_id'] == m_id3:
            assert message['is_pinned'] is True


def test_message_pin_invalid():
    '''
    Test:
        - Pinning with invalid token
        - Pinning with invalid message id
        - Pinning messages whilst not being in channel

    Scenario:
        - Two users register (owner and user)
        - Owner creates a private channel and sends a message
        - Test attempts to pin this message with invalid token and message id
        - User tries to pin the message without being in the channel
        - Test checks that the message is not pinned
    '''
    clear()

    # Owner and User register
    f_owner = auth_register('johnmonkeyson@gmail.com', 'bananayummy', 'John', 'Monkeyson')
    f_user = auth_register('stevenson@gmail.com', 'ihatebananas', 'Steven', 'Stevenson')

    # Owner creates private channel
    f_channel = channels_create(f_owner['token'], 'Private Channel', False)

    # Owner sends message in f_channel (Private Channel)
    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'hELLO wOORLD!')['message_id']

    # Invalid token
    with pytest.raises(AccessError):
        message_pin('thisisaninvalidtoken!', m_id1)

    # Invalid message id
    with pytest.raises(InputError):
        message_pin(f_owner['token'], -29424)

    # Pinning message without being in the channel
    with pytest.raises(AccessError):
        message_pin(f_user['token'], m_id1)

    # Get messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is not pinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is False


def test_message_pin_permission():
    '''
    Test:
        - Pinning a message without being the owner of the channel

    Scenario:
        - Two users register (owner and user), owner creates a private channel and
        invites user to channel
        - Owner sends a message
        - User tries to pin message(should not work)
        - Test checks that the message is not pinned
        - Owner pins the message (should work)
        - Test checks that the message is actually pinned
    '''
    clear()

    # Owner and User register
    f_owner = auth_register('peter@com.com', 'djiffgjigi22', 'Peter', 'Peterson')
    f_user = auth_register('useruserson@gmail.com', 'helloworld', 'User', 'Userson')

    # Owner creates private channel
    f_channel = channels_create(f_owner['token'], 'Private Channel', False)

    # Owner invites f_user to channel
    channel_invite(f_owner['token'], f_channel['channel_id'], f_user['u_id'])

    # Owner sends message in f_channel (Private Channel)
    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'hELLO wOORLD!')['message_id']

    # User tries to pin the message but is not an owner (no permission)
    with pytest.raises(AccessError):
        message_pin(f_user['token'], m_id1)

    # Get messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is not pinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is False

    # Owner pins the message
    message_pin(f_owner['token'], m_id1)

    # Update messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is pinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is True


def test_message_pin_already_pinned():
    '''
    Test:
        - Pinning an already pinned message

    Scenario:
        - Owner registers
        - Owner creates a channel
        - Owner sends a message
        - Owner pins the message
        - Test checks that message is actually pinned
        - Owner tries to pin the same message again
    '''
    clear()

    # Owner registers
    f_owner = auth_register('peterson@hotmail.com', 'djiffgjigi22', 'Peter', 'Peterson')

    # Owner creates private channel
    f_channel = channels_create(f_owner['token'], 'Private Channel', False)

    # Owner sends message in f_channel (Private Channel)
    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'hELLO wOORLD!')['message_id']

    # Owner pins the message
    message_pin(f_owner['token'], m_id1)

    # Get messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is pinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is True

    # Try to pin already pinned message
    with pytest.raises(InputError):
        message_pin(f_owner['token'], m_id1)


def test_message_unpin_valid():
    '''
    Test:
        - Unpinning a message normally

    Scenario:
        - Two users register (owner and user)
        - Owner creates a private channel and invites user
        - Owner and user send messages
        - Test checks that all messages are not pinned
        - Owner pins 1 message
        - Test checks that the message is pinned
        - Owner unpins message
        - Test checks that all messages are unpinned
    '''
    clear()

    # Owner and User register
    f_owner = auth_register('johnmonkeyson@gmail.com', 'bananayummy', 'John', 'Monkeyson')
    f_user = auth_register('stevenson@gmail.com', 'ihatebananas', 'Steven', 'Stevenson')

    # Owner creates private channel
    f_channel = channels_create(f_owner['token'], 'Private Channel', False)

    # Owner invites f_user to channel
    channel_invite(f_owner['token'], f_channel['channel_id'], f_user['u_id'])

    # Owner and user send messages in f_channel (Private Channel)
    message_send(f_owner['token'], f_channel['channel_id'], 'hELLO wOORLD!')
    message_send(f_owner['token'], f_channel['channel_id'], 'hello?')

    m_id3 = message_send(f_user['token'], f_channel['channel_id'], 'pin this pls')['message_id']

    message_send(f_user['token'], f_channel['channel_id'], 'bye world')

    # Get messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that all messages are not pinned
    for message in messages:
        assert message['is_pinned'] is False

    # Owner pins a message
    message_pin(f_owner['token'], m_id3)

    # Update messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is pinned
    for message in messages:
        if message['message_id'] == m_id3:
            assert message['is_pinned'] is True

    # Owner unpins the message
    message_unpin(f_owner['token'], m_id3)

    # Update messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that no messages are pinned
    for message in messages:
        assert message['is_pinned'] is False


def test_message_unpin_invalid():
    '''
    Test:
        - Unpinning with invalid token
        - Unpinning messages whilst not being in channel
        - Unpinning with invalid message id

    Scenario:
        - Two users register (owner and user)
        - Owner creates a private channel and sends a message
        - Owner pins message
        - Test tries to unpin message with invalid token
        - Test tries to unpin message with an invalid message id
        - User1 tries to unpin message without being in the channel
        - Test checks that the message is still pinned
    '''
    clear()

    # Owner and User register
    f_owner = auth_register('johnmonkeyson@gmail.com', 'bananayummy', 'John', 'Monkeyson')
    f_user = auth_register('stevenson@gmail.com', 'ihatebananas', 'Steven', 'Stevenson')

    # Owner creates private channel
    f_channel = channels_create(f_owner['token'], 'Private Channel', False)

    # Owner sends message in f_channel (Private Channel)
    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'hELLO wOORLD!')['message_id']

    # Owner pins message
    message_pin(f_owner['token'], m_id1)

    # Invalid token
    with pytest.raises(AccessError):
        message_unpin('thisisaninvalidtoken!', m_id1)

    # Invalid message id
    with pytest.raises(InputError):
        message_unpin(f_owner['token'], -4224)

    # Unpinning message without being in the channel
    with pytest.raises(AccessError):
        message_unpin(f_user['token'], m_id1)

    # Get messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is still pinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is True


def test_message_unpin_permission():
    '''
    Test:
        - Unpinning a message without being the owner of the channel

    Scenario:
        - Two users register (owner and user), owner creates a private channel and
    invites user to channel
        - Owner sends a message
        - Owner pins the message
        - User tries to unpin message (should not work)
        - Test checks that the message is still pinned
        - Owner unpins the message (should work)
        - Test checks that the message is not pinned anymore
    '''
    clear()

    # Owner and User register
    f_owner = auth_register('peter@com.com', 'djiffgjigi22', 'Peter', 'Peterson')
    f_user = auth_register('useruserson@gmail.com', 'helloworld', 'User', 'Userson')

    # Owner creates private channel
    f_channel = channels_create(f_owner['token'], 'Private Channel', False)

    # Owner invites f_user to channel
    channel_invite(f_owner['token'], f_channel['channel_id'], f_user['u_id'])

    # Owner sends message in f_channel (Private Channel)
    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'hELLO wOORLD!')['message_id']

    # Owner pins message
    message_pin(f_owner['token'], m_id1)

    # User tries to unpin message (should not work)
    with pytest.raises(AccessError):
        message_unpin(f_user['token'], m_id1)

    # Get messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is still pinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is True

    # Owner unpins the message
    message_unpin(f_owner['token'], m_id1)

    # Update messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is not pinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is False


def test_message_unpin_already_unpinned():
    '''
    Test:
        - Unpinning an already unpinned message

    Scenario:
        - Owner registers
        - Owner creates a channel
        - Owner sends a message
        - Owner pins the message
        - Test checks that the message is pinned
        - Owner unpins message
        - Owner tries to unpin message again (should not work)
        - Test checks that the message is unpinned
    '''
    clear()

    # Owner registers
    f_owner = auth_register('peterson@hotmail.com', 'djiffgjigi22', 'Peter', 'Peterson')

    # Owner creates private channel
    f_channel = channels_create(f_owner['token'], 'Private Channel', False)

    # Owner sends message in f_channel (Private Channel)
    m_id1 = message_send(f_owner['token'], f_channel['channel_id'], 'hELLO wOORLD!')['message_id']

    # Owner pins the message
    message_pin(f_owner['token'], m_id1)

    # Get messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Check that the message is pinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is True

    # Owner unpins message
    message_unpin(f_owner['token'], m_id1)

    # Update messages in channel
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)['messages']

    # Owner tries to unpin unpinned message
    with pytest.raises(InputError):
        message_unpin(f_owner['token'], m_id1)

    # Check that the message is unpinned
    for message in messages:
        if message['message_id'] == m_id1:
            assert message['is_pinned'] is False
            