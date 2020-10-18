import pytest
from auth import auth_register
from channel import channel_invite
from channels import channels_create
from message import message_send, message_remove, message_edit
from other import clear, search
from error import InputError, AccessError

def test_search_invalid():
    '''
    Testing invalid cases for search
    '''
    clear()
    f_owner = auth_register('admin@gmail.com', 'password', 'Bob', 'Bob')
    f_channel = channels_create(f_owner['token'], 'Channel 1', True)
    message_send(f_owner['token'], f_channel['channel_id'], 'First message')

    # Invalid token
    with pytest.raises(AccessError):
        search(f_owner['token'] + 'padding', 'First')

    # Empty messages (shouldn't be sent anyways)
    with pytest.raises(InputError):
        message_send(f_owner['token'], f_channel['channel_id'], '')
        messages = search(f_owner['token'], '')
        assert len(messages) == 0

def test_search_valid_substring():
    '''
    Testing valid substring search functionality for search
    '''
    clear()
    f_owner = auth_register('admin@gmail.com', 'password', 'Bob', 'Bob')
    f_channel = channels_create(f_owner['token'], 'Channel 1', True)
    random_user = auth_register('random@gmail.com', 'password', 'Random', 'User')
    channel_invite(f_owner['token'], f_channel['channel_id'], random_user['u_id'])

    msg = message_send(f_owner['token'], f_channel['channel_id'], 'First message')

    # Test exact match
    messages = search(f_owner['token'], 'First message')['messages']
    assert len(messages) == 1
    assert messages[0]['message_id'] == msg['message_id']
    assert messages[0]['u_id'] == f_owner['u_id']

    # Test substring
    messages = search(f_owner['token'], 'First')['messages']
    assert len(messages) == 1
    assert messages[0]['message_id'] == msg['message_id']
    assert messages[0]['u_id'] == f_owner['u_id']

    # Edited message
    message_edit(f_owner['token'], msg['message_id'], 'Test message')
    messages = search(f_owner['token'], 'First')['messages']
    assert len(messages) == 0

    # Removed message
    message_remove(f_owner['token'], msg['message_id'])
    messages = search(f_owner['token'], 'First message')['messages']
    assert len(messages) == 0

    # Test substring
    for multiple in range(1, 51):
        # f_owner and random_user sent
        message_send(f_owner['token'], f_channel['channel_id'], 'A' * multiple)
        message_send(random_user['token'], f_channel['channel_id'], 'A' * multiple)
        # f_owner searched
        messages = search(f_owner['token'], 'A')['messages']
        assert len(messages) == multiple * 2
        # random_user searched
        messages = search(random_user['token'], 'A')['messages']
        assert len(messages) == multiple * 2

def test_search_valid_global():
    '''
    Testing search works across all channels a user is in
    '''
    clear()
    f_owner = auth_register('admin@gmail.com', 'password', 'Bob', 'Bob')
    common_channel = channels_create(f_owner['token'], 'Common Channel', True)
    f_channel = channels_create(f_owner['token'], 'Crib', True)

    # Test includes private channels as well
    random_user = auth_register('random@gmail.com', 'password', 'Random', 'User')
    private_channel = channels_create(random_user['token'], 'SSH', False)

    channel_invite(f_owner['token'], common_channel['channel_id'], random_user['u_id'])

    # Messages sent to common channels
    for i in range(1, 51):
        message_send(f_owner['token'], common_channel['channel_id'], 'F')
        message_send(random_user['token'], common_channel['channel_id'], 'R')
        f_messages = search(f_owner['token'], 'F')['messages']
        r_messages = search(f_owner['token'], 'R')['messages']
        assert len(f_messages) == i and len(r_messages) == i

    # Messages sent to personal channels (includes messages in common_channel)
    for i in range(1, 51):
        message_send(f_owner['token'], f_channel['channel_id'], 'F')
        message_send(random_user['token'], private_channel['channel_id'], 'R')
        f_messages = search(f_owner['token'], 'F')['messages']
        r_messages = search(random_user['token'], 'R')['messages']
        assert len(f_messages) == 50 + i and len(r_messages) == 50 + i

    # From Flockr Owner
    f_messages = search(f_owner['token'], 'F')['messages']
    assert len(f_messages) == 100
    r_messages = search(f_owner['token'], 'R')['messages']
    assert len(r_messages) == 50
    # From Random User
    f_messages = search(random_user['token'], 'F')['messages']
    assert len(f_messages) == 50
    r_messages = search(random_user['token'], 'R')['messages']
    assert len(r_messages) == 100
