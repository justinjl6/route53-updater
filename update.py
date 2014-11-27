#!/usr/bin/python3

program     = 'route53-updater'
version     = 'v1'
description = 'A simple program to update AWS Route53 DNS records.'
author      = 'Justin Lambe'
email       = 'jlambe@gmail.com'
url         = 'https://github.com/justinjl6/route53-updater'

import os
import sys

################################################################################
# User variables

## None yet


################################################################################
# System variables

base_dir    = os.path.dirname( os.path.abspath( __file__ ) )
config_file = base_dir + '/aws.cfg'
dyn_api     = 'http://ipinfo.io/ip'
epilog = '''
Setting a value of "dynamic" will force record type to "A" and use this hosts
public internet facing IP address as the records value.
'''

################################################################################
# Imports

sys.path.append( base_dir + '/boto' )

import argparse
import boto.route53 as route53
import configparser
import re
import stat
import urllib


################################################################################
# Config variables

## Default values
aws_access_key      = 'replace_me'
aws_secret_key      = 'replace_me'
route53_default_ttl = '300'

## Initialise configparser
config = configparser.ConfigParser()

try:
    ## Try to read variables from config file
    config.read( config_file )
    aws_access_key  = config['aws']['access_key']
    aws_secret_key  = config['aws']['secret_key']
except:
    ## Create/repair config file
    config['aws'] = {}
    config['aws']['access_key'] = aws_access_key
    config['aws']['secret_key'] = aws_secret_key
    config['route53'] = {}
    config['route53']['default_ttl']    = route53_default_ttl
    with open( config_file, 'w' ) as fh:
        config.write( fh )
    os.chmod( config_file, stat.S_IWRITE | stat.S_IREAD )
    sys.exit( 1 )


################################################################################
# Parse arguments

## Initialise the parser
parser = argparse.ArgumentParser( prog = program, description = description, epilog = epilog )
parser.set_defaults( type = 'A' )
parser.add_argument( '-z', required = True,  dest = 'zone',   help = 'Zone name. E.G.: example.com.')
parser.add_argument( '-r', required = True,  dest = 'record', help = 'Record name. E.G.: www.example.com.' )
parser.add_argument( '-t', required = False, dest = 'type',   help = 'Record type. E.G.: A, MX, SRV, etc' )
parser.add_argument( '-v', required = True,  dest = 'value',  help = 'Record data. E.G.: IP Address, MX host, dynamic, etc' )

args = parser.parse_args()


################################################################################
# Variable validation

## Check AWS access/secret keys
if ( aws_access_key == 'replace_me' ) or ( aws_secret_key == 'replace_me' ):
    print( 'Please edit the config file and set your AWS access/secret keys.' )
    print( config_file )
    sys.exit( 1 )

if ( args.value == 'dynamic' ):
    print( 'Determining my dynamic internet IP ( ' + dyn_api + ' )' )
    response = urllib.request.urlopen( dyn_api )
    args.value = response.read().rstrip().decode('utf-8')
    args.type = 'A'


################################################################################
# Connect to Route 53

conn    = route53.connection.Route53Connection( aws_access_key, aws_secret_key )

## Establish connection to route53 and retrieve the zone
print( 'Retrieving zone ' + args.zone )
zone    = conn.get_hosted_zone_by_name( args.zone )
zone_id = zone.get('GetHostedZoneResponse').get('HostedZone').get('Id')
zone_id = re.sub( '.*/', '', zone_id )
print( 'Zone ID is ' + zone_id )

## Define the record
record  = route53.record.Record( name = args.record, type = args.type, ttl = route53_default_ttl )
record.add_value( args.value )

## Apply the changes
change  = route53.record.ResourceRecordSets( connection = conn, hosted_zone_id = zone_id )
change.add_change_record( 'UPSERT', record )

print( 'Setting ' + args.record + ' to { ' + args.type + ' => ' + args.value + ' }' )

try:
    change.commit()
except:
    print( 'Failed Hard :(' )
else:
    print( 'Great Success!' )


################################################################################

