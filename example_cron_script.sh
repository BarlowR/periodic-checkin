#!/bin/bash

<path_to_python_env>/python <path_to_dir>/simple_check_in.py
        --to_email <to_email> \
        --sender_email <sender_email> \
        --periodic <daily, weekly, or monthly> \
        --template_folder <path_to_templates> \
        --auth <path_to_auth_credentials_for_sender_email> \
        // Optional : 
        --subject_prefix <Prefix to add to email subject line>
