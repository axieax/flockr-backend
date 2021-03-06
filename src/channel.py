''' Import required modules '''
from data import user_with_token, user_with_id, channel_with_id
from error import InputError, AccessError

def channel_invite(token, channel_id, u_id):
    '''
    Invites a user (with user id u_id) to join a channel with ID channel_id.
    Once invited the user is added to the channel immediately
    Input: token (str), channel_id (int), u_id (int)
    Output: empty dict
    '''
    # Retrieve data
    auth_user = user_with_token(token)
    channel = channel_with_id(channel_id)
    invited_user = user_with_id(u_id)

    # Error check
    if auth_user is None:
        raise AccessError('Invalid token')
    elif channel is None:
        raise InputError('Invalid channel_id')
    elif invited_user is None:
        raise InputError('Invalid u_id')
    elif auth_user not in channel.get_all_members():
        raise AccessError('Authorised user not a member of channel')

    # Append invited user to all_members (if they're not already a member)
    if invited_user not in channel.get_all_members():
        channel.get_all_members().append(invited_user)

    return {
    }


def channel_details(token, channel_id):
    '''
    Given a Channel with ID channel_id that the authorised user is part of,
    provide basic details about the channel
    Input: token (str), channel_id (int)
    Output: dict
    '''
    # Retrieve data
    auth_user = user_with_token(token)
    channel = channel_with_id(channel_id)

    # Error check
    if auth_user is None:
        raise AccessError('Invalid token')
    elif channel is None:
        raise InputError('Invalid channel_id')
    elif auth_user not in channel.get_all_members():
        raise AccessError('Authorised user not a member of channel')

    return {
        'name': channel.get_name(),
        'owner_members': [
            {
                'u_id': owner.get_u_id(),
                'name_first': owner.get_name_first(),
                'name_last': owner.get_name_last(),
                'profile_img_url': owner.get_profile_img_url(),
            }
            for owner in channel.get_owner_members()
        ],
        'all_members': [
            {
                'u_id': member.get_u_id(),
                'name_first': member.get_name_first(),
                'name_last': member.get_name_last(),
                'profile_img_url': member.get_profile_img_url(),
            }
            for member in channel.get_all_members()
        ],
    }


def channel_messages(token, channel_id, start):
    '''
    Given a Channel with ID channel_id that the authorised user is part of,
    return up to 50 messages between index "start" and "start + 50".
    Message with index 0 is the most recent message in the channel.
    This function returns a new index "end" which is the value of "start + 50", or,
    if this function has returned the least recent messages in the channel,
    returns -1 in "end" to indicate there are no more messages to load after this return.
    Input: token (str), channel_id (int), start (int)
    Ouput: dict
    '''
    # Retrieve data
    auth_user = user_with_token(token)
    channel = channel_with_id(channel_id)

    # Error check
    if auth_user is None:
        raise AccessError('Invalid token')
    elif channel is None:
        raise InputError('Invalid channel_id')
    elif auth_user not in channel.get_all_members():
        raise AccessError('Authorised user not a member of channel')
    elif start < 0 or start > len(channel.get_messages()):
        raise InputError('Invalid start index')

    # Messages originally ordered chronologically -
    # reverse and retrieve a maximum of 50 most recent messages
    messages = list(reversed(channel.get_messages()))[start : start + 50]
    if len(messages) == 0:
        # The end is reached there are no messages
        end = -1
    else:
        # The end is also reached if the first message (id) is included in messages
        first_message_id = channel.get_messages()[0].get_message_id()
        first_message_reached = any(message.get_message_id() == first_message_id
                                    for message in messages)
        end = -1 if first_message_reached else start + 50

    return {
        'messages': [
            {
                'message_id': message.get_message_id(),
                'u_id': message.get_sender().get_u_id(),
                'time_created': message.get_time_created(),
                'message': message.get_message(),
                'reacts': [
                    {
                        'react_id': react.get_react_id(),
                        'u_ids': [reactor.get_u_id() for reactor in react.get_reactors()],
                        'is_this_user_reacted': auth_user in react.get_reactors(),
                    }
                    for react in message.get_reacts()
                ],
                'is_pinned': message.get_is_pinned(),
            }
            for message in messages
        ],
        'start': start,
        'end': end,
    }


def channel_leave(token, channel_id):
    '''
    Given a channel ID, the user removed as a member of this channel
    Input: token (str), channel_id (int)
    Output: empty dict
    '''
    # Retrieve data
    auth_user = user_with_token(token)
    channel = channel_with_id(channel_id)

    # Error check
    if auth_user is None:
        raise AccessError('Invalid token')
    elif channel is None:
        raise InputError('Invalid channel_id')
    elif auth_user not in channel.get_all_members():
        raise AccessError('Authorised user not a member of channel')

    # Remove user from all_members
    channel.get_all_members().remove(auth_user)

    # Attempt to remove user from owner_members if they are an owner
    if auth_user in channel.get_owner_members():
        channel.get_owner_members().remove(auth_user)

    return {
    }


def channel_join(token, channel_id):
    '''
    Given a channel_id of a channel that the authorised user can join, adds them to that channel
    Input: token (str), channel_id (int)
    Output: empty dict
    '''
    # Retrieve data
    channel = channel_with_id(channel_id)
    auth_user = user_with_token(token)

    # Error check
    if auth_user is None:
        raise AccessError('Invalid token')
    elif channel is None:
        raise InputError('Invalid channel_id')
    elif not channel.get_is_public() and auth_user.get_permission_id() != 1:
        raise AccessError('Private channel and authorised user is not Flockr owner')

    # Adds user to channel if not already in channel (don't want to add duplicate users to list)
    if auth_user not in channel.get_all_members():
        channel.get_all_members().append(auth_user)

    return {
    }


def channel_addowner(token, channel_id, u_id):
    '''
    Make user with user id u_id an owner of this channel
    Input: token (str), channel_id (int), u_id (int)
    Output: empty dict
    '''
    # Retrieve data
    auth_user = user_with_token(token)
    channel = channel_with_id(channel_id)
    new_owner = user_with_id(u_id)

    # Error check
    if auth_user is None:
        raise AccessError('Invalid token')
    elif channel is None:
        raise InputError('Invalid channel_id')
    elif new_owner is None or new_owner not in channel.get_all_members():
        raise AccessError('Invalid u_id or user is not a member in the channel')
    elif auth_user not in channel.get_owner_members() and auth_user.get_permission_id() != 1:
        raise AccessError('Authorised user is not an owner of channel and not Flockr owner')
    elif auth_user not in channel.get_all_members():
        # Note that Flockr owner may not be a channel member
        raise AccessError('Authorised user is not a member in the channel')
    elif new_owner in channel.get_owner_members():
        raise InputError('User to be added as an owner is already an owner in the channel')

    # Add user as owner
    channel.get_owner_members().append(new_owner)

    return {
    }


def channel_removeowner(token, channel_id, u_id):
    '''
    Remove user with user id u_id an owner of this channel
    Input: token (str), channel_id (int), u_id (int)
    Output: empty dict
    '''
    # Retrieve data
    auth_user = user_with_token(token)
    channel = channel_with_id(channel_id)
    old_owner = user_with_id(u_id)

    # Error check
    if auth_user is None:
        raise AccessError('Invalid token')
    elif channel is None:
        raise InputError('Invalid channel_id')
    elif old_owner is None:
        raise AccessError('Invalid u_id')
    elif auth_user not in channel.get_owner_members() and auth_user.get_permission_id() != 1:
        raise AccessError('Authorised user is not an owner of channel and not Flockr owner')
    elif auth_user not in channel.get_all_members():
        # Flockr owner may not be a channel member
        raise AccessError('Authorised user is not a member in the channel')
    elif old_owner not in channel.get_owner_members():
        raise InputError('User to be removed as an owner was not an owner in the channel')

    # Remove owner
    channel.get_owner_members().remove(old_owner)

    return {
    }


# Extra function
def channel_kick(token, channel_id, u_id):
    '''
    Remove user with user id u_id as a member of the channel
    Input: token (str), channel_id (int), u_id (int)
    Output: empty dict
    '''
    # Retrieve data
    auth_user = user_with_token(token)
    channel = channel_with_id(channel_id)
    old_user = user_with_id(u_id)

    # Error check
    if auth_user is None:
        raise AccessError('Invalid token')
    elif channel is None:
        raise InputError('Invalid channel_id')
    elif old_user is None:
        raise AccessError('Invalid u_id')
    elif auth_user not in channel.get_all_members():
        # Flockr owner may not be a channel member
        raise AccessError('Authorised user is not a member in the channel')
    elif auth_user not in channel.get_owner_members() and auth_user.get_permission_id() != 1:
        raise AccessError('Authorised user is not an owner of channel and not Flockr owner')
    elif old_user in channel.get_owner_members():
        # User cannot be an owner of the channel
        raise InputError('User to be kicked cannot be an owner in the channel')
    elif old_user not in channel.get_all_members():
        raise InputError('User to be kicked is not a member in the channel')

    # Remove owner
    channel.get_all_members().remove(old_user)

    return {
    }
