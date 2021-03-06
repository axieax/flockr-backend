''' Test file for standup.py '''
import time
import pytest
from standup import standup_start, standup_active, standup_send
from channels import channels_create
from channel import channel_join, channel_messages
from auth import auth_register
from error import InputError, AccessError
from other import clear


def test_standup_start_valid():
    '''
    Test validly starting a standup
    '''
    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Owner')
    f_channel = channels_create(f_owner['token'], 'Test Channel', True)

    # Start standup for 5 seconds
    t_finish1 = standup_start(f_owner['token'], f_channel['channel_id'], 5)['time_finish']

    # Check standup is active
    standup_details = standup_active(f_owner['token'], f_channel['channel_id'])
    assert standup_details['is_active'] is True
    # Check that time_finish of both standup_start and standup_active are the same
    t_finish2 = standup_details['time_finish']
    assert t_finish1 == t_finish2

    # Check standup is not active after standup ends
    time.sleep(6)
    standup_details = standup_active(f_owner['token'], f_channel['channel_id'])
    assert standup_details['is_active'] is False


def test_standup_start_invalid():
    '''
    Test invalidly starting a standup
    '''
    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Owner')
    f_channel = channels_create(f_owner['token'], 'Test Channel', True)

    # Invalid token
    with pytest.raises(AccessError):
        standup_start('', f_channel['channel_id'], 5)

    # Channel ID is not a valid channel
    with pytest.raises(InputError):
        standup_start(f_owner['token'], f_channel['channel_id'] + 100, 5)

    # User not member of channel
    f_user = auth_register('user@gmail.com', 'password', 'Random', 'User')
    with pytest.raises(AccessError):
        standup_start(f_user['token'], f_channel['channel_id'], 5)

    # Invalid standup length
    with pytest.raises(InputError):
        standup_start(f_owner['token'], f_channel['channel_id'], 0)
    with pytest.raises(InputError):
        standup_start(f_owner['token'], f_channel['channel_id'], -5)

    # Active standup is currently running
    standup_start(f_owner['token'], f_channel['channel_id'], 5)
    with pytest.raises(InputError):
        standup_start(f_owner['token'], f_channel['channel_id'], 5)


def test_standup_active_valid():
    '''
    Test validly checking if a standup is active
    '''
    clear()
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Owner')
    f_channel = channels_create(f_owner['token'], 'Test Channel', True)

    # Check standup_active returns correct values with no active standup
    standup_details = standup_active(f_owner['token'], f_channel['channel_id'])
    assert standup_details['is_active'] is False
    assert standup_details['time_finish'] is None

    # Start standup for 5 seconds
    t_finish1 = standup_start(f_owner['token'], f_channel['channel_id'], 5)['time_finish']

    # Check standup_active returns correct values during a standup
    standup_details = standup_active(f_owner['token'], f_channel['channel_id'])
    assert standup_details['is_active'] is True
    # Check that time_finish of both standup_start and standup_active are the same
    t_finish2 = standup_details['time_finish']
    assert t_finish1 == t_finish2

    # Check standup_active returns correct values after standup ends
    time.sleep(6)
    standup_details = standup_active(f_owner['token'], f_channel['channel_id'])
    assert standup_details['is_active'] is False
    assert standup_details['time_finish'] is None


def test_standup_active_invalid():
    '''
    Test invalidly checking if a standup is active
    '''
    clear()
    # Set up users and channel
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Owner')
    f_user = auth_register('user@gmail.com', 'password', 'Random', 'User')
    f_channel = channels_create(f_owner['token'], 'Test Channel', True)

    # Invalid token
    with pytest.raises(AccessError):
        standup_active('', f_channel['channel_id'])

    # Channel ID is not a valid channel
    with pytest.raises(InputError):
        standup_active(f_owner['token'], f_channel['channel_id'] + 100)

    # Authorised user is not a member of the channel
    with pytest.raises(AccessError):
        standup_active(f_user['token'], f_channel['channel_id'])


def test_standup_send_valid():
    '''
    Test validly sending messages to get buffered in the standup queue
    '''
    clear()
    # Set up users and channel
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Owner')
    f_user = auth_register('user@gmail.com', 'password', 'Random', 'User')
    f_channel = channels_create(f_owner['token'], 'Test Channel', True)
    channel_join(f_user['token'], f_channel['channel_id'])

    # Start standup for 5 seconds
    standup_start(f_owner['token'], f_channel['channel_id'], 5)

    # Users send messages during the standup
    message1 = 'F' * 1000
    message2 = 'X' * 1000
    for _ in range(0, 3):
        standup_send(f_owner['token'], f_channel['channel_id'], message1)
        standup_send(f_user['token'], f_channel['channel_id'], message2)

    # Check only one message (containing all the standup messages) is sent after the standup ends
    time.sleep(6)
    messages = channel_messages(f_owner['token'], f_channel['channel_id'], 0)
    assert len(messages['messages']) == 1


def test_standup_send_invalid():
    '''
    Test invalidly sending messages to get buffered in the standup queue
    '''
    clear()
    # Set up users and channel
    f_owner = auth_register('owner@gmail.com', 'password', 'Flockr', 'Owner')
    f_user = auth_register('user@gmail.com', 'password', 'Random', 'User')
    f_channel = channels_create(f_owner['token'], 'Test Channel', True)

    # Active standup is not currently running in the channel
    with pytest.raises(InputError):
        standup_send(f_owner['token'], f_channel['channel_id'], 'Test message!')

    # Start a standup
    standup_start(f_owner['token'], f_channel['channel_id'], 7)

    # Invalid token
    with pytest.raises(AccessError):
        standup_send('', f_channel['channel_id'], 'Test message!')

    # Channel ID is not a valid channel
    with pytest.raises(InputError):
        standup_send(f_owner['token'], f_channel['channel_id'] + 100, 'Test message!')

    # Message lengths
    with pytest.raises(InputError):
        standup_send(f_owner['token'], f_channel['channel_id'], '')
    message = 'F' * 1001
    with pytest.raises(InputError):
        standup_send(f_owner['token'], f_channel['channel_id'], message)
    with pytest.raises(InputError):
        standup_send(f_owner['token'], f_channel['channel_id'], message + 'F')

    # Authorised user is not a member of the channel
    with pytest.raises(AccessError):
        standup_send(f_user['token'], f_channel['channel_id'], 'Test message!')
