''' Import required modules '''
import pytest
import re
from subprocess import Popen, PIPE
import signal
from time import sleep
import requests
import json
from echo_http_test import url

##################
## HTTP channel ##
##################
def test_http_channel_invite(url):
    '''
    HTTP test for channel_invite

    Test:
        - Inviting to channel with invalid channel
        - Inviting to channel with invalid user id
        - Inviting to channel without being in the channel
        - Inviting to channel validly
    
    Scenario:
        - Owner and user register
        - Owner sets up channel
        - Owner invites user to channel with invalid channel id
        - Owner with invalid user id invites user
        - User invites owner without being in channel
        - Owner invites user successfully
    '''
    assert requests.delete(url + 'clear').status_code == 200

    # Register owner
    resp = requests.post(url + 'auth/register', json={
        'email': 'owner@gmail.com',
        'password': 'password',
        'name_first': 'John',
        'name_last': 'Smith',
    })
    assert resp.status_code == 200
    owner = resp.json()

    # Register user
    resp = requests.post(url + 'auth/register', json={
        'email': 'user@gmail.com',
        'password': 'password',
        'name_first': 'Steve',
        'name_last': 'Jackson',
    })
    assert resp.status_code == 200
    user = resp.json()

    # Set up channel
    resp = requests.post(url + 'channels/create', json={
        'token': owner['token'],
        'name': 'Test Channel',
        'is_public': True,
    })
    assert resp.status_code == 200
    channel_id = resp.json()['channel_id']

    # channel_id does not refer to a valid channel
    resp = requests.post(url + 'channel/invite', json ={
        'token': owner['token'],
        'channel_id': channel_id + 100,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 400

    # u_id does not refer to a valid channel
    resp = requests.post(url + 'channel/invite', json ={
        'token': owner['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'] + 100,
    })
    assert resp.status_code == 400

    # Authorised user not in channel
    resp = requests.post(url + 'channel/invite', json ={
        'token': user['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 400

    # Invite the user successfully
    resp = requests.post(url + 'channel/invite', json ={
        'token': owner['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 200


def test_http_channel_details(url):
    '''
    HTTP test for channel_details

    Test:
        - Getting channel details with invalid channel id
        - Getting channel details without being in the channel
        - Getting channel details successfully
    
    Scenario:
        - Owner and user register
        - Owner sets up channel
        - Owner tries to get channel details with invalid channel id
        - User tries to get channel details without being in channel
        - Owner invites user to channel
        - User successfully sees channel details
    '''
    assert requests.delete(url + 'clear').status_code == 200

    # Register owner
    resp = requests.post(url + 'auth/register', json={
        'email': 'liambrown@gmail.com',
        'password': 'password',
        'name_first': 'Liam',
        'name_last': 'Brown',
    })
    assert resp.status_code == 200
    owner = resp.json()

    # Register user
    resp = requests.post(url + 'auth/register', json={
        'email': 'victorzhang@gmail.com',
        'password': 'password',
        'name_first': 'Victor',
        'name_last': 'Zhang',
    })
    assert resp.status_code == 200
    user = resp.json()

    # Set up channel
    resp = requests.post(url + 'channels/create', json={
        'token': owner['token'],
        'name': 'Test Channel',
        'is_public': True,
    })
    assert resp.status_code == 200
    channel_id = resp.json()['channel_id']

    # channel_id does not refer to a valid channel
    resp = requests.get(url + 'channel/details', params={
        'token': owner['token'],
        'channel_id': channel_id + 100,
    })
    assert resp.status_code == 400

    # Authorised user not in channel
    resp = requests.get(url + 'channel/details', params={
        'token': user['token'],
        'channel_id': channel_id,
    })
    assert resp.status_code == 400

    # Invite the user successfully
    resp = requests.post(url + 'channel/invite', json={
        'token': owner['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 200

    # User can now view the channel details
    resp = requests.get(url + 'channel/details', params={
        'token': user['token'],
        'channel_id': channel_id,
    })
    assert resp.status_code == 200

    payload = resp.json()
    # Ignore profile_img_url from checks
    for member in payload['owner_members']:
        del member['profile_img_url']
    for member in payload['all_members']:
        del member['profile_img_url']

    assert payload == {
        'name': 'Test Channel',
        'owner_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Liam',
                'name_last': 'Brown',
            }
        ],
        'all_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Liam',
                'name_last': 'Brown',
            },
            {
                'u_id': user['u_id'],
                'name_first': 'Victor',
                'name_last': 'Zhang',
            }
        ],
    }


def test_http_channel_messages(url):
    '''
    HTTP test for channel_messages

    Test:
        - Getting channel messages with invalid token
        - Getting channel messages without being in channel
        - Getting channel messages with invalid start index
        - Getting channel messages validly
    
    Scenario:
        - Owner and user register
        - Owner sets up channel
        - Test tries to get channel messages with invalid token
        - User tries to get channel messages without being in channel
        - Owner tries to get channel messages with invalid start index
        - Owner gets channel messages successfully
    '''
    assert requests.delete(url + 'clear').status_code == 200

    # Register users
    resp = requests.post(url + 'auth/register', json={
        'email': 'admin@gmail.com',
        'password': 'password',
        'name_first': 'Admin',
        'name_last': 'User',
    })
    assert resp.status_code == 200
    admin_user = resp.json()

    resp = requests.post(url + 'auth/register', json={
        'email': 'random@gmail.com',
        'password': 'password',
        'name_first': 'Random',
        'name_last': 'User',
    })
    assert resp.status_code == 200
    random_user = resp.json()

    # Set up channel
    resp = requests.post(url + 'channels/create', json={
        'token': admin_user['token'],
        'name': 'Admin Channel',
        'is_public': True,
    })
    assert resp.status_code == 200
    admin_channel_id = resp.json()['channel_id']

    # Invalid token
    resp = requests.get(url + 'channel/messages', params={
        'token': '',
        'channel_id': admin_channel_id,
        'start': 0,
    })
    assert resp.status_code == 400

    # User not in channel
    resp = requests.get(url + 'channel/messages', params={
        'token': random_user['token'],
        'channel_id': admin_channel_id,
        'start': 0,
    })
    assert resp.status_code == 400

    # Invalid channel_id
    resp = requests.get(url + 'channel/messages', params={
        'token': admin_user['token'],
        'channel_id': admin_channel_id + 1,
        'start': 0,
    })
    assert resp.status_code == 400

    # Test start index - testing 50 messages
    for message_sent in range(1, 51):
        # Send message
        resp = requests.post(url + 'message/send', json={
            'token': admin_user['token'],
            'channel_id': admin_channel_id,
            'message': f'Message {message_sent}',
        })
        assert resp.status_code == 200
        # Invalid start index
        resp = requests.get(url + 'channel/messages', params={
            'token': admin_user['token'],
            'channel_id': admin_channel_id,
            'start': message_sent + 1,
        })
        assert resp.status_code == 400
        # Valid request from start index 0
        resp = requests.get(url + 'channel/messages', params={
            'token': admin_user['token'],
            'channel_id': admin_channel_id,
            'start': 0,
        })
        assert resp.status_code == 200
        payload = resp.json()
        assert len(payload['messages']) == message_sent
        assert payload['start'] == 0
        assert payload['end'] == -1
        # Valid request from previous message
        resp = requests.get(url + 'channel/messages', params={
            'token': admin_user['token'],
            'channel_id': admin_channel_id,
            'start': message_sent - 1,
        })
        assert resp.status_code == 200
        payload = resp.json()
        assert len(payload['messages']) == 1
        assert payload['start'] == message_sent - 1
        assert payload['end'] == -1
        # Valid request from current message
        resp = requests.get(url + 'channel/messages', params={
            'token': admin_user['token'],
            'channel_id': admin_channel_id,
            'start': message_sent,
        })
        assert resp.status_code == 200
        payload = resp.json()
        assert len(payload['messages']) == 0
        assert payload['start'] == message_sent
        assert payload['end'] == -1

    # Test message 51
    resp = requests.post(url + 'message/send', json={
        'token': admin_user['token'],
        'channel_id': admin_channel_id,
        'message': 'Message 51',
    })
    assert resp.status_code == 200

    resp = requests.get(url + 'channel/messages', params={
        'token': admin_user['token'],
        'channel_id': admin_channel_id,
        'start': 0,
    })
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload['messages']) == 50
    assert payload['start'] == 0
    assert payload['end'] == 50

    resp = requests.get(url + 'channel/messages', params={
        'token': admin_user['token'],
        'channel_id': admin_channel_id,
        'start': 1,
    })
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload['messages']) == 50
    assert payload['start'] == 1
    assert payload['end'] == -1


def test_http_channel_leave(url):
    '''
    HTTP test for channel_leave

    Test:
        - Leaving a channel with an invalid channel id
        - Leaving a channel without being in the channel
        - Leaving a channel validly
    
    Scenario:
        - Owner and user register
        - User tries to leave channel with invalid channel id
        - User tries to leave channel without being in channel
        - User joins owner's channel
        - User leaves channel successfully
    '''
    assert requests.delete(url + 'clear').status_code == 200
    
    # Register owner
    resp = requests.post(url + 'auth/register', json={
        'email': 'petermichaels@gmail.com',
        'password': 'password',
        'name_first': 'Peter',
        'name_last': 'Michaels',
    })
    assert resp.status_code == 200
    owner = resp.json()

    # Register user
    resp = requests.post(url + 'auth/register', json={
        'email': 'kimwilliams@gmail.com',
        'password': 'password',
        'name_first': 'Kim',
        'name_last': 'Williams',
    })
    assert resp.status_code == 200
    user = resp.json()

    # Set up channel
    resp = requests.post(url + 'channels/create', json={
        'token': owner['token'],
        'name': 'Test Channel',
        'is_public': True,
    })
    assert resp.status_code == 200
    channel_id = resp.json()['channel_id']

    # channel_id does not refer to a valid channel
    resp = requests.post(url + 'channel/leave', json ={
        'token': user['token'],
        'channel_id': channel_id + 100,
    })
    assert resp.status_code == 400

    # Authorised user not in channel
    resp = requests.post(url + 'channel/leave', json={
        'token': user['token'],
        'channel_id': channel_id,
    })
    assert resp.status_code == 400

    # User joins channel
    resp = requests.post(url + 'channel/join', json={
        'token': user['token'],
        'channel_id': channel_id,
    })
    assert resp.status_code == 200

    # User leaves channel successfully
    resp = requests.post(url + 'channel/leave', json={
        'token': user['token'],
        'channel_id': channel_id,
    })
    assert resp.status_code == 200

    # Check that the details are correct
    resp = requests.get(url + 'channel/details', params={
        'token': owner['token'],
        'channel_id': channel_id,
    })
    assert resp.status_code == 200
    payload = resp.json()

    # Ignore profile_img_url from checks
    for member in payload['owner_members']:
        del member['profile_img_url']
    for member in payload['all_members']:
        del member['profile_img_url']
    
    assert payload == {
        'name': 'Test Channel',
        'owner_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Peter',
                'name_last': 'Michaels',
            },
        ],
        'all_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Peter',
                'name_last': 'Michaels',
            },
        ],
    }


def test_http_channel_join(url):
    '''
    HTTP test for channel_join

    Test:
        - Joining a channel with an invalid channel id
        - Joining a private channel with no invitation
        - Joining a channel validly
    
    Scenario:
        - Owner and user register
        - Owner sets up private and public channel
        - User tries to join channel with invalid channel id
        - User tries to join private channel with no invite
        - User joins public channel successfully
    '''
    assert requests.delete(url + 'clear').status_code == 200
    
    # Register owner
    resp = requests.post(url + 'auth/register', json={
        'email': 'petermichaels@gmail.com',
        'password': 'password',
        'name_first': 'Peter',
        'name_last': 'Michaels',
    })
    assert resp.status_code == 200
    owner = resp.json()

    # Register user
    resp = requests.post(url + 'auth/register', json={
        'email': 'kimwilliams@gmail.com',
        'password': 'password',
        'name_first': 'Kim',
        'name_last': 'Williams',
    })
    assert resp.status_code == 200
    user = resp.json()

    # Set up a public and a private channel
    resp = requests.post(url + 'channels/create', json={
        'token': owner['token'],
        'name': 'Public Channel',
        'is_public': True,
    })
    assert resp.status_code == 200
    public_channel_id = resp.json()['channel_id']

    resp = requests.post(url + 'channels/create', json={
        'token': owner['token'],
        'name': 'Private Channel',
        'is_public': False,
    })
    assert resp.status_code == 200
    private_channel_id = resp.json()['channel_id']

    # channel_id does not refer to a valid channel
    resp = requests.post(url + 'channel/join', json ={
        'token': user['token'],
        'channel_id': public_channel_id + 100,
    })
    assert resp.status_code == 400

    # channel_id refers to a private channel (authorised user is not global owner)
    resp = requests.post(url + 'channel/join', json={
        'token': user['token'],
        'channel_id': private_channel_id,
    })
    assert resp.status_code == 400

    # User joins channel
    resp = requests.post(url + 'channel/join', json={
        'token': user['token'],
        'channel_id': public_channel_id,
    })
    assert resp.status_code == 200

    # Check that the details are correct
    resp = requests.get(url + 'channel/details', params={
        'token': user['token'],
        'channel_id': public_channel_id,
    })
    assert resp.status_code == 200
    payload = resp.json()
    # Ignore profile_img_url from checks
    for member in payload['owner_members']:
        del member['profile_img_url']
    for member in payload['all_members']:
        del member['profile_img_url']

    assert payload == {
        'name': 'Public Channel',
        'owner_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Peter',
                'name_last': 'Michaels',
            },
        ],
        'all_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Peter',
                'name_last': 'Michaels',
            },
            {
                'u_id': user['u_id'],
                'name_first': 'Kim',
                'name_last': 'Williams',
            },
        ],
    }


def test_http_channel_addowner(url):
    '''
    HTTP test for channel_addowner

    Test:
        - Adding a user as an owner with an invalid channel id
        - Adding a user as an owner whilst already being an owner
        - Adding a user as an owner without user being in the channel
    
    Scenario:
        - Owner and user register
        - Owner sets up channel
        - User joins channel
        - Owner tries to add user as owner with invalid channel id
        - Owner tries to add owner as owner
        - Owner tries to add user as owner without user being in channel
    '''
    assert requests.delete(url + 'clear').status_code == 200

    # Register owner
    resp = requests.post(url + 'auth/register', json={
        'email': 'bobsmith@gmail.com',
        'password': 'password',
        'name_first': 'Bob',
        'name_last': 'Smith',
    })
    assert resp.status_code == 200
    owner = resp.json()

    # Register user
    resp = requests.post(url + 'auth/register', json={
        'email': 'jesschen@gmail.com',
        'password': 'password',
        'name_first': 'Jess',
        'name_last': 'Chen',
    })
    assert resp.status_code == 200
    user = resp.json()

    # Set up channel
    resp = requests.post(url + 'channels/create', json={
        'token': owner['token'],
        'name': 'Test Channel',
        'is_public': True,
    })
    assert resp.status_code == 200
    channel_id = resp.json()['channel_id']

    # Join channel
    resp = requests.post(url + 'channel/join', json={
        'token': user['token'],
        'channel_id': channel_id
    })
    assert resp.status_code == 200

    # channel_id does not refer to a valid channel
    resp = requests.post(url + 'channel/addowner', json ={
        'token': owner['token'],
        'channel_id': channel_id + 100,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 400

    # User is already an owner
    resp = requests.post(url + 'channel/addowner', json={
        'token': owner['token'],
        'channel_id': channel_id,
        'u_id': owner['u_id'],
    })
    assert resp.status_code == 400

    # Authorised user not in channel
    resp = requests.post(url + 'channel/addowner', json={
        'token': user['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 400

    # Add the user as an owner successfully
    resp = requests.post(url + 'channel/addowner', json={
        'token': owner['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 200

    # Check that the details are correct
    resp = requests.get(url + 'channel/details', params={
        'token': user['token'],
        'channel_id': channel_id,
    })
    assert resp.status_code == 200
    payload = resp.json()
    # Ignore profile_img_url from checks
    for member in payload['owner_members']:
        del member['profile_img_url']
    for member in payload['all_members']:
        del member['profile_img_url']

    assert payload == {
        'name': 'Test Channel',
        'owner_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Bob',
                'name_last': 'Smith',
            },
            {
                'u_id': user['u_id'],
                'name_first': 'Jess',
                'name_last': 'Chen',
            }
        ],
        'all_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Bob',
                'name_last': 'Smith',
            },
            {
                'u_id': user['u_id'],
                'name_first': 'Jess',
                'name_last': 'Chen',
            }
        ],
    }


def test_http_channel_removeowner(url):
    '''
    HTTP test for channel_removeowner

    Test:
        - Removing user as owner without being an owner
        - Removing user as owner with an invalid channel id
        - Successfully removing owner
    
    Scenario:
        - Owner and user register
        - Owner sets up channel
        - User joins channel
        - Owner tries to remove user as owner without them being an owner
        - User tries to remove owner but is not an owner
        - Owner adds user as an owner
        - Owner tries to remove user as owner with an invalid channel id
        - Owner removes user as an owner successfully
    '''
    assert requests.delete(url + 'clear').status_code == 200

    # Register owner
    resp = requests.post(url + 'auth/register', json={
        'email': 'bobsmith@gmail.com',
        'password': 'password',
        'name_first': 'Bob',
        'name_last': 'Smith',
    })
    assert resp.status_code == 200
    owner = resp.json()

    # Register user
    resp = requests.post(url + 'auth/register', json={
        'email': 'jesschen@gmail.com',
        'password': 'password',
        'name_first': 'Jess',
        'name_last': 'Chen',
    })
    assert resp.status_code == 200
    user = resp.json()

    # Set up channel
    resp = requests.post(url + 'channels/create', json={
        'token': owner['token'],
        'name': 'Test Channel',
        'is_public': True,
    })
    assert resp.status_code == 200
    channel_id = resp.json()['channel_id']

    # Join channel
    resp = requests.post(url + 'channel/join', json={
        'token': user['token'],
        'channel_id': channel_id
    })
    assert resp.status_code == 200

    # User is not an owner
    resp = requests.post(url + 'channel/removeowner', json={
        'token': owner['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 400

    # Authorised user is not an owner
    resp = requests.post(url + 'channel/removeowner', json={
        'token': user['token'],
        'channel_id': channel_id,
        'u_id': owner['u_id'],
    })
    assert resp.status_code == 400

    # Add the user as an owner
    resp = requests.post(url + 'channel/addowner', json={
        'token': owner['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 200

    # channel_id does not refer to a valid channel
    resp = requests.post(url + 'channel/removeowner', json={
        'token': owner['token'],
        'channel_id': channel_id + 100,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 400

    # Remove the user as an owner successfully
    resp = requests.post(url + 'channel/removeowner', json={
        'token': owner['token'],
        'channel_id': channel_id,
        'u_id': user['u_id'],
    })
    assert resp.status_code == 200

    # Check that the details are correct
    resp = requests.get(url + 'channel/details', params={
        'token': user['token'],
        'channel_id': channel_id,
    })
    assert resp.status_code == 200
    payload = resp.json()
    # Ignore profile_img_url from checks
    for member in payload['owner_members']:
        del member['profile_img_url']
    for member in payload['all_members']:
        del member['profile_img_url']

    assert payload == {
        'name': 'Test Channel',
        'owner_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Bob',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': owner['u_id'],
                'name_first': 'Bob',
                'name_last': 'Smith',
            },
            {
                'u_id': user['u_id'],
                'name_first': 'Jess',
                'name_last': 'Chen',
            }
        ],
    }
