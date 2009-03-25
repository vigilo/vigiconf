################################################################################
## $Id$
##
## Functions.pm : PERL function package, Customizable functions for the Collector
##                Nagios Plugin
##		
## Copyright (C) 2006-2007 CS-SI
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#################################################################################

package Functions;
use strict;
use warnings;
use Data::Dumper;
require Exporter;
use vars qw(@ISA @EXPORT $VERSION);
@ISA=qw(Exporter);
@EXPORT= qw( %Functions %Primitive );
$VERSION = 1.0;

# Hashmap of generic multipurpose routines
our %Primitive = (
"date2Time"		=> sub {
    # converts a sysuptime string into a number of seconds
	my $date = shift;

	if ($date =~ /^(\d+) days?, (\d+):(\d+):(\d+)\.(\d+)/)
	{
		return (((((($1 * 24) + $2) * 60) + $3) * 60) + $4);
	}
	if ($date =~ /^(\d+) hours?, (\d+):(\d+)\.(\d+)/)
	{
		return (((($1 * 60) + $2) * 60) + $3);
	}
	if ($date =~ /^(\d+) minutes?, (\d+)\.(\d+)/)
	{
		return (($1 * 60) + $2) ;
	}
	if ($date =~ /^(\d+)\.(\d+) seconds?/)
	{
		return ($1);
	}
	return 0;
},
"checkOIDVal"   => sub {
    # checks whether the value returned by an SNMP GET or WALKS seems correct
    my $val = shift;
    return 0 unless defined $val;
    return ($val =~ /noSuch(Object|Instance)|endOfMibView|NULL/ ? 0 : 1)
},
"isOutOfBounds" => sub {
    # checks if a value fits is out the "Nagios standard Threshold range"
    # see http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT
	my ($value,$st)=@_;
	my $inside=( ($st =~ /^@/) ? 1 : 0 );
	$st =~ s/^@//;
	$st=":" if ($st eq "");
	if ( $st =~ /:/)
	{ # two limits have been given
		my ($low,$upp)=split(/:/,$st);
		return $inside if (! $low && ! $upp);
		return ($inside ? $value <= $upp : $value > $upp) ? 1 : 0 if ($low =~ /^~?$/);
		return ($inside ? $value >= $low : $value < $low) ? 1 : 0 if($upp eq "" );
		return -1 if($low>$upp);
		return( $inside ? ($value >= $low && $value <= $upp) : ($value > $upp || $value < $low) ) ? 1 : 0;
	}
	return ($value >= 0 && $value <= $st) ? 1 : 0 if $inside;
	return ($value < 0 || $value > $st) ? 1 : 0;
},
"thresholdIt" => sub {
    # checks the correctness of the given value, with the warn and crit thresholds
    # see http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT for thresholds syntax
	my ($value,$warnThresh,$critThresh,$caption,$Primitive)=@_;
    $caption=$caption || "%s";
	return("CRITICAL", sprintf("CRITICAL: $caption", $value))   if ($Primitive->{"isOutOfBounds"}->($value, $critThresh));
	return("WARNING",  sprintf("WARNING: $caption",   $value))  if ($Primitive->{"isOutOfBounds"}->($value, $warnThresh));
	return('OK',       sprintf("OK: $caption",       $value));
},
"lookup" => sub {
    # looks for a given pattern in an OID subtree
    # which is supposed to be one-level deep
    # pattern can be a portion of a regexp
    # returns the index of the OID first matching the pattern
	my ($response,$where,$key)=@_;
	foreach my $OID (keys %{$response})
	{
		if ($OID =~ /^$where\./)
		{
			if ($response->{$OID} =~ /^${key}\000?$/)
			{
				$OID =~ /\.(\d+)$/; # Got it
				return $1;
			}
		}
	}
	return -1;
},
"lookupMultiple" => sub {
    # looks for a given pattern in an OID subtree
    # which is supposed to be one-level deep
    # pattern can be a portion of a regexp
    # returns the list of indexes matching
	my ($response,$where,$key)=@_;
    my @indexes;
	foreach my $OID (keys %{$response})
	{
		if ($OID =~ /^$where\./)
		{
			if ($response->{$OID} =~ /^${key}\000?$/)
			{
				$OID =~ /\.(\d+)$/; # Got it
				push @indexes,$1;
			}
		}
	}
	return @indexes;
},
"lookupText" => sub {
    # looks for the index betwen an an OID subtree
    # and the numeric representation of the text
    # returns this index
	my ($response,$where,$text)=@_;
    my $numeric = "";
    foreach my $char (split(//,$text))
    {
        $numeric = "$numeric.".ord($char);
    }
	foreach my $OID (keys %{$response})
	{
        
		if ($OID =~ /^$where\.(\d+$numeric)/)
		{
            return $1;
		}
	}
	return -1;
},
"resultMap" => sub {
    # maps the result given an array of hashmaps describing a regex and a state and message to produce
    # fallback is returned is no match occured
	my ($val,$valFilters,$fallbackState,$fallbackMessage)=@_;
	foreach my $i (@$valFilters)
	{
		if ($val =~ /$$i{"pattern"}/)
		{
			return ($$i{"state"},$$i{"message"});
		}
	}
	return ($fallbackState,$fallbackMessage);
},
"genericHW" => sub {
    my ($response,$descrOID,$stateOID,$okValue,$caption,$debug)=@_;
	my $state="OK";
    my @msg;
    my $nbItems=0;
	foreach my $OID (keys %{$response})
	{
		if ($OID =~ /^$stateOID\.(\d+)/) {
            my $index = $1;
			if ($response->{$OID} =~ /^${okValue}\000?$/) {
				print "ignoring \"".$response->{"$descrOID.$index"}."\" $caption that seems OK\n" if ($debug);
                $nbItems++;
				next;
			}
			push @msg,$response->{"$descrOID.$index"};
			$state="CRITICAL";
		}
	}
	return ("UNKNOWN","UNKNOWN: no $caption found.") if ($nbItems == 0);
	return ("OK","OK: $nbItems $caption(s) OK") if ($state eq "OK");
	return ("CRITICAL","CRITICAL: Failed $caption(s): ".join(',',@msg));
},
"genericIfOperStatus"		=> sub {
	my ($interfaceName, $ifAdminStatus, $ifOperStatus, $ifAlias, $ifIndex, $adminWarn, $dormantWarn, $Primitive, $debug)=@_;

	my ($state, $answer);
	my $alias = '';
	if ($Primitive->{"checkOIDVal"}->($ifAlias) && $ifAlias ne '')
	{
		$alias = "($ifAlias)";
	}
	else
	{
		$alias = "(index $ifIndex)";
	}

	$answer = "Interface $interfaceName $alias";
	# if AdminStatus is down - some one made a consious effort to change config
	if ( not ($ifAdminStatus == 1) )
	{
		$answer .= " is administratively down.";
		if ( not defined $adminWarn or $adminWarn eq "w" )
		{
			$state = 'WARNING';
		}
		elsif ( $adminWarn eq "i" )
		{
			$state = 'OK';
		}
		elsif ( $adminWarn eq "c" )
		{
			$state = 'CRITICAL';
		}
		else
		{ # If wrong value for authProto, say warning
			$state = 'WARNING';
		}
	} 
	## Check operational status
	elsif ( $ifOperStatus == 2 )
	{
			$state = 'CRITICAL';
			$answer .= " is down.";
	}
	elsif ( $ifOperStatus == 5 )
	{
		$answer .= " is dormant.";
		if (defined $dormantWarn )
		{
			if ($dormantWarn eq "w")
			{
				$state = 'WARNING';
			}
			elsif($dormantWarn eq "c")
			{
				$state = 'CRITICAL';
			}
			elsif($dormantWarn eq "i")
			{
				$state = 'OK';
			}
		}
		else
		{
			# dormant interface  - but warning/critical/ignore not requested
			$state = 'CRITICAL';
		}
	}
	elsif( $ifOperStatus == 6 )
	{
		$state = 'CRITICAL';
		$answer .= " notPresent - possible hotswap in progress.";
	}
	elsif ( $ifOperStatus == 7 )
	{
		$state = 'CRITICAL';
		$answer .= " down due to lower layer being down.";
	}
	elsif ( $ifOperStatus == 3 || $ifOperStatus == 4  )
	{
		$state = 'CRITICAL';
		$answer .= " down (testing/unknown).";
	}
	else
	{
			$state = 'OK';
			$answer .= " is up.";
	}

	return ($state, "$state: $answer");
},
);

#############################################################################################################################################################
#############################################################################################################################################################
#############################################################################################################################################################
#############################################################################################################################################################
#############################################################################################################################################################
#############################################################################################################################################################
#############################################################################################################################################################

our %Functions = (
"thresholds_OID_simple"	=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $OID         = (split('/',$variables->[0]))[1];
	my $warnThresh 	= $parameters->[0];
	my $critThresh	= $parameters->[1];
	my $caption 	= $parameters->[2] || "%s";

	my $value	    = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($value);
	return $Primitive->{"thresholdIt"}->($value,$warnThresh,$critThresh,$caption, $Primitive);
},
"thresholds_OID_plus_max"	=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $OID		= (split('/',$variables->[0]))[1];
	my $maxOID	= (split('/',$variables->[1]))[1];
	my $value	    = $response->{$OID};
	my $maxValue	= $response->{$maxOID};
	my $warnThresh	= $parameters->[0];
	my $critThresh	= $parameters->[1];
	my $caption	    = $parameters->[2] || "usage: %2.2f%%";

	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($value);
	return ("UNKNOWN","UNKNOWN: OID $maxOID not found") unless $Primitive->{"checkOIDVal"}->($maxValue);
	return $Primitive->{"thresholdIt"}->($value*100.0/$maxValue,$warnThresh,$critThresh,$caption,$Primitive);
},
"thresholds_mult"	=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $OID1		= (split('/',$variables->[0]))[1];
	my $OID2	    = (split('/',$variables->[1]))[1];
	my $val1	    = $response->{$OID1};
	my $val2	    = $response->{$OID2};
	my $warnThresh	= $parameters->[0];
	my $critThresh	= $parameters->[1];
	my $caption	    = $parameters->[2] || "%s";

	return ("UNKNOWN","UNKNOWN: OID $OID1 not found") unless $Primitive->{"checkOIDVal"}->($val1);
	return ("UNKNOWN","UNKNOWN: OID $OID2 not found") unless $Primitive->{"checkOIDVal"}->($val2);
	return $Primitive->{"thresholdIt"}->($val1*$val2,$warnThresh,$critThresh,$caption,$Primitive);
},
"simple_factor"	=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $OID         = (split('/',$variables->[0]))[1];
	my $warnThresh 	= $parameters->[0];
	my $critThresh	= $parameters->[1];
	my $factor	    = $parameters->[2];
	my $caption 	= $parameters->[3] || "%s";

	my $value	    = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($value);
	return $Primitive->{"thresholdIt"}->($value*$factor,$warnThresh,$critThresh,$caption, $Primitive);
},
"table"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $name	    = $parameters->[0];
	my $warnThresh 	= $parameters->[1];
	my $critThresh	= $parameters->[2];
	my $caption 	= $parameters->[3] || "%s";
	my $OID	        = (split('/',$variables->[0]))[1];
	my $descrOID	= (split('/',$variables->[1]))[1];

	# Get the index
	my $index = $Primitive->{"lookup"}->($response,$descrOID,$name);
	return ("UNKNOWN","UNKNOWN: $name not found in $descrOID") if ($index == -1);
    my $value=$response->{"$OID.$index"};
	return ("UNKNOWN","UNKNOWN: OID $OID.$index not found") unless $Primitive->{"checkOIDVal"}->($value);
	return $Primitive->{"thresholdIt"}->($value, $warnThresh, $critThresh, $caption, $Primitive);
},
"table_factor"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $name        = $parameters->[0];
	my $warnThresh  = $parameters->[1];
	my $critThresh  = $parameters->[2];
	my $factor      = $parameters->[3];
	my $caption     = $parameters->[4] || "%s";
	my $OID	        = (split('/',$variables->[0]))[1];
	my $descrOID	= (split('/',$variables->[1]))[1];

	# Get the index
	my $index = $Primitive->{"lookup"}->($response,$descrOID,$name);
	return ("UNKNOWN","UNKNOWN: $name not found in $descrOID") if ($index == -1);
    my $value=$response->{"$OID.$index"};
	return ("UNKNOWN","UNKNOWN: OID $OID.$index not found") unless $Primitive->{"checkOIDVal"}->($value);
	return $Primitive->{"thresholdIt"}->($value * $factor, $warnThresh, $critThresh, $caption, $Primitive);
},
"table_mult"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $name	    = $parameters->[0];
	my $warnThresh 	= $parameters->[1];
	my $critThresh	= $parameters->[2];
	my $caption 	= $parameters->[3] || "%s";
	my $val1OID	    = (split('/',$variables->[0]))[1];
	my $val2OID	    = (split('/',$variables->[1]))[1];
	my $descrOID	= (split('/',$variables->[2]))[1];

	# Get the index
	my $index = $Primitive->{"lookup"}->($response,$descrOID,$name);
	return ("UNKNOWN","UNKNOWN: $name not found in $descrOID") if ($index == -1);
    my $val1=$response->{"$val1OID.$index"};
    my $val2=$response->{"$val2OID.$index"};
	return ("UNKNOWN","UNKNOWN: OID $val1OID.$index not found") unless $Primitive->{"checkOIDVal"}->($val1);
	return ("UNKNOWN","UNKNOWN: OID $val2OID.$index not found") unless $Primitive->{"checkOIDVal"}->($val2);
	return $Primitive->{"thresholdIt"}->($val1*$val2, $warnThresh, $critThresh, $caption, $Primitive);
},
"table_used_free"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $name	    = $parameters->[0];
	my $warnThresh 	= $parameters->[1];
	my $critThresh	= $parameters->[2];
	my $caption 	= $parameters->[3] || "%f%%";
	my $usedOID	    = (split('/',$variables->[0]))[1];
	my $freeOID	    = (split('/',$variables->[1]))[1];
	my $descrOID	= (split('/',$variables->[2]))[1];

	# Get the index
	my $index = $Primitive->{"lookup"}->($response,$descrOID,$name);
	return ("UNKNOWN","UNKNOWN: $name not found in $descrOID") if ($index == -1);
    my $used=$response->{"$usedOID.$index"};
    my $free=$response->{"$freeOID.$index"};
	return ("UNKNOWN","UNKNOWN: OID $usedOID.$index not found") unless $Primitive->{"checkOIDVal"}->($used);
	return ("UNKNOWN","UNKNOWN: OID $freeOID.$index not found") unless $Primitive->{"checkOIDVal"}->($free);
	return $Primitive->{"thresholdIt"}->(($used*100.0)/($free+$used), $warnThresh, $critThresh, $caption, $Primitive);
},
"table_mult_factor"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $name	    = $parameters->[0];
	my $warnThresh 	= $parameters->[1];
	my $critThresh	= $parameters->[2];
	my $factor      = $parameters->[3];
	my $caption     = $parameters->[4] || "%s";
	my $val1OID	    = (split('/',$variables->[0]))[1];
	my $val2OID	    = (split('/',$variables->[1]))[1];
	my $descrOID	= (split('/',$variables->[2]))[1];

	# Get the index
	my $index = $Primitive->{"lookup"}->($response,$descrOID,$name);
	return ("UNKNOWN","UNKNOWN: $name not found in $descrOID") if ($index == -1);
    my $val1=$response->{"$val1OID.$index"};
    my $val2=$response->{"$val2OID.$index"};
	return ("UNKNOWN","UNKNOWN: OID $val1OID.$index not found") unless $Primitive->{"checkOIDVal"}->($val1);
	return ("UNKNOWN","UNKNOWN: OID $val2OID.$index not found") unless $Primitive->{"checkOIDVal"}->($val2);
	return $Primitive->{"thresholdIt"}->($val1 * $val2 * $factor, $warnThresh, $critThresh, $caption, $Primitive);
},
"sysUpTime"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	
	my $criticalTime	= $parameters->[0] || 400;
	my $warnTime		= $parameters->[1] || 900;
	my $sysUpTimeOID	= (split('/',$variables->[0]))[1];
	my $timestamp		= 0;
	my $sysUpTime		= $response->{$sysUpTimeOID};

	return ("UNKNOWN","UNKNOWN: OID $sysUpTimeOID not found") unless $Primitive->{"checkOIDVal"}->($sysUpTime);
	if ($timestamp = $Primitive->{"date2Time"}->($sysUpTime))
	{
        return $Primitive->{"thresholdIt"}->($timestamp,"\@$warnTime","\@$criticalTime","sysUpTime is $sysUpTime (%d s)",$Primitive);
	}
	return ('UNKNOWN', "UNKNOWN: unable to understand sysUpTime $sysUpTime");
},
"ifOperStatus"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $interface		= $parameters->[0];
	my $interfaceName	= $parameters->[1];
	my $adminWarn		= $parameters->[2] || 'w';
	my $dormantWarn		= $parameters->[3] || 'c';
	my $ifDescrOID		= (split('/',$variables->[0]))[1];
	my $ifAdminStatusOID	= (split('/',$variables->[1]))[1];
	my $ifOperStatusOID	= (split('/',$variables->[2]))[1];
	my $ifAliasOID		= (split('/',$variables->[3]))[1];

	my ($state, $answer);
	my $ifIndex = $Primitive->{"lookup"}->($response,$ifDescrOID,$interface);
	return ("UNKNOWN","Interface name ($interface) not found in ifDescr") if ($ifIndex == -1);

	my $ifAdminStatus 	= $response->{"$ifAdminStatusOID.$ifIndex"};
	my $ifOperStatus 	= $response->{"$ifOperStatusOID.$ifIndex"};
	my $ifAlias		    = $response->{"$ifAliasOID.$ifIndex"};
	return ("UNKNOWN","UNKNOWN: OID $ifAdminStatusOID.$ifIndex not found") unless $Primitive->{"checkOIDVal"}->($ifAdminStatus);
	return ("UNKNOWN","UNKNOWN: OID $ifOperStatusOID.$ifIndex not found")  unless $Primitive->{"checkOIDVal"}->($ifOperStatus);
	return $Primitive->{"genericIfOperStatus"}->($interfaceName, $ifAdminStatus, $ifOperStatus, $ifAlias, $ifIndex, $adminWarn, $dormantWarn, $Primitive, $debug);
},
"ifOperStatus_ISG"   => sub {
	my $parameters          = shift;
	my $variables           = shift;
	my $response            = shift;
	my $debug               = shift || 0;

	my $ifIndex             = $parameters->[0];
	my $invertStatus        = $parameters->[1] || 0;
	my @ifDescrOID          = split ('/',$variables->[0]);
	my @ifOperStatusOID     = split ('/',$variables->[1]);

	my $interface           = $response->{"$ifDescrOID[1].$ifIndex"} || "not found";
	my $ifOperStatus        = $response->{"$ifOperStatusOID[1].$ifIndex"};
	my ($state, $answer);

	if ($ifIndex == -1 || ! defined $ifOperStatus) {
		$answer = "Interface name ($interface) not found in ifDescr";
		$state = "UNKNOWN";
		return ($state, $answer);
	}
	# FIXME : ce comportement doit etre gere par la correlation
	#         etat OK si tunnel DOWN si FW secondaire
	if ($host::Host{'hostname'} =~ /\w{5}-FW-[DN]C\d{2}-(\d)/) {
		$invertStatus = 1 if ($1 == 2);
	}

	$answer = "Tunnel $interface (index $ifIndex)";
	## Check operational status
	if ( $ifOperStatus == 0 ) {
		if ($invertStatus == 1) {
			$state = 'OK';
			$answer .= " is down.";
		} elsif ($invertStatus == 0) {
			$state = 'CRITICAL';
			$answer .= " is down.";
		} else {
			$state = 'UNKNOWN';
			$answer = "Bad invertStatus value ($invertStatus)";
		}
	} elsif ($ifOperStatus == 1) {
		if ($invertStatus == 1) {
			$state = 'CRITICAL';
			$answer .= " is up.";
		} elsif ($invertStatus == 0) {
			$state = 'OK';
			$answer .= " is up.";
		} else {
			$state = 'UNKNOWN';
			$answer = "Bad invertStatus value ($invertStatus)";
		}
	} else {
		$state = 'UNKNOWN';
		$answer .= "ifOperStatus value ($ifOperStatus) not known";
	}

	return ($state, $answer);
},
"staticIfOperStatus"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $ifIndex		= $parameters->[0];
	my $interfaceName	= $parameters->[1];
	my $adminWarn		= $parameters->[2] || 'w';
	my $dormantWarn		= $parameters->[3] || 'c';
	my $ifDescrOID		= (split('/',$variables->[0]))[1];
	my $ifAdminStatusOID	= (split('/',$variables->[1]))[1];
	my $ifOperStatusOID	= (split('/',$variables->[2]))[1];
	my $ifAliasOID		= (split('/',$variables->[3]))[1];

	my ($state, $answer);

	my $ifAdminStatus 	= $response->{"$ifAdminStatusOID.$ifIndex"};
	my $ifOperStatus 	= $response->{"$ifOperStatusOID.$ifIndex"};
	my $ifAlias		= $response->{"$ifAliasOID.$ifIndex"};
	my $ifDescr		= $response->{"$ifDescrOID.$ifIndex"};
	return ("UNKNOWN","UNKNOWN: OID $ifAdminStatusOID.$ifIndex not found") unless $Primitive->{"checkOIDVal"}->($ifAdminStatus);
	return ("UNKNOWN","UNKNOWN: OID $ifOperStatusOID.$ifIndex not found")  unless $Primitive->{"checkOIDVal"}->($ifOperStatus);
	if ($Primitive->{"checkOIDVal"}->($ifDescrOID))
	{
		$interfaceName = "$ifDescr $interfaceName";
	}
	return $Primitive->{"genericIfOperStatus"}->($interfaceName, $ifAdminStatus, $ifOperStatus, $ifAlias, $ifIndex, $adminWarn, $dormantWarn, $Primitive, $debug);
},
"storage"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $partition		= $parameters->[0];
	my $warnThresh		= $parameters->[1];
	my $critThresh		= $parameters->[2];
	my $percent 		= $parameters->[3];
	my $hrStorageDescrOID           = (split('/',$variables->[0]))[1];
	my $hrStorageAllocationUnitsOID = (split('/',$variables->[1]))[1];
	my $hrStorageSizeOID	        = (split('/',$variables->[2]))[1];
	my $hrStorageUsedOID	        = (split('/',$variables->[3]))[1];

	my $hrIndex = $Primitive->{"lookup"}->($response,$hrStorageDescrOID,$partition);
	return ("UNKNOWN","Partition name ($partition) not found in hrStorageDescr") if ($hrIndex == -1);

	my $hrAU  = $response->{"$hrStorageAllocationUnitsOID.$hrIndex"};
	my $hrS   = $response->{"$hrStorageSizeOID.$hrIndex"};
	my $hrU	  = $response->{"$hrStorageUsedOID.$hrIndex"};
	return ("UNKNOWN","UNKNOWN: OID $hrStorageAllocationUnitsOID.$hrIndex not found") unless $Primitive->{"checkOIDVal"}->($hrAU);
	return ("UNKNOWN","UNKNOWN: OID $hrStorageUsedOID.$hrIndex not found") unless $Primitive->{"checkOIDVal"}->($hrU);
	return ("UNKNOWN","UNKNOWN: OID $hrStorageSizeOID.$hrIndex not found") unless $Primitive->{"checkOIDVal"}->($hrS);
	my $usedBytes = $hrU*$hrAU;
	my $maxBytes = $hrS*$hrAU;
	return ("UNKNOWN","UNKNOWN: 0 byte Allocation units for storage $partition") if $maxBytes == 0;
    if ($percent)
    {
        my $usagePercentage = $usedBytes*100.0/$maxBytes;
        return $Primitive->{"thresholdIt"}->($usagePercentage,$warnThresh,$critThresh,"Usage: ".sprintf("%.2f",$usedBytes/1024/1024)." MB (%2.2f%%)", $Primitive);
    }
    else
    {
        my $freeBytes = $maxBytes - $usedBytes;
        my $freePercentage = $freeBytes*100.0/$maxBytes;
        $freePercentage = sprintf("%2.2f%%%%",$freePercentage);
        return $Primitive->{"thresholdIt"}->($freeBytes,"@".($warnThresh*1024*1024),"@".($critThresh*1024*1024),"Usage: %d Bytes free ($freePercentage)", $Primitive);
    }
},
"walk_grep_count"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $pattern		= $parameters->[0];
	my $warnThresh		= $parameters->[1];
	my $critThresh		= $parameters->[2];
	my $caption		= $parameters->[3] || "%d occurences";
	my $walk		= (split('/',$variables->[0]))[1];

	my $value;
	$value=0;
	# Get the ifIndex
	foreach my $OID (keys %{$response})
	{
		if ($OID =~ /^$walk\./)
		{
			if ($response->{$OID} =~ /^$pattern\000?$/)
			{
				$value++;
			}
		}
	}
	return $Primitive->{"thresholdIt"}->($value,$warnThresh,$critThresh,$caption,$Primitive);
},
"ciscoFans"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,1,"Fan",$debug);
},
"ciscoTemps"	=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,1,"Temperature sensor",$debug);
},
"ciscoPsus"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,1,"PSU",$debug);
},
"hpFans"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,"[12]","Fan",$debug);
},
"hpTemps"	=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,2,"Temperature sensor",$debug);
},
"hpPsus"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,2,"PSU",$debug);
},
"hpRaid"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,2,"RAID Controller",$debug);
},
"winsvc"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $svcName		= $parameters->[0];
	my $stateOID		= (split('/',$variables->[0]))[1];
    my $svcOID = length($svcName);
    $svcName =~ /(.)$/;
    my $lastByte = ord($1);
	my $svcState  = $response->{"$stateOID.$lastByte"};
    # If the service is stopped, it disappears from the list...
	return ("CRITICAL","CRITICAL: service is down or not installed") unless $Primitive->{"checkOIDVal"}->($svcState);
    # OK = 1, others = WARNING
    my $i=[
        {pattern=>"1", state=>"OK",      message=>"OK: service is active"},
        {pattern=>"2", state=>"WARNING", message=>"WARNING: service is in continue-pending state"},
        {pattern=>"3", state=>"WARNING", message=>"WARNING: service is in pause-pending state"},
        {pattern=>"4", state=>"WARNING", message=>"WARNING: service is paused"},
    ];
    return $Primitive->{"resultMap"}->($svcState,$i,"UNKNOWN","UNKNOWN: state $svcState");
},
"solLMSensorsPsus"  => sub {
    # LM-SENSORS-MIB::lmMiscSensorsDevice.4 = STRING: ps0_act
    # LM-SENSORS-MIB::lmMiscSensorsDevice.5 = STRING: ps0_service
    # LM-SENSORS-MIB::lmMiscSensorsDevice.6 = STRING: ps0_ok2rm
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $valueOID	    = (split('/',$variables->[0]))[1];
	my $descrOID	    = (split('/',$variables->[1]))[1];
    my %expectedValues=(
        'ps\d+_act'     => 1,
        'ps\d+_service' => 0,
        'ps\d+_ok2rm'   => 0,
    );
    my @msg;
    my $wrong=0;
    my $nbIndics=0;
	foreach my $OID (keys %{$response})
	{
		if ($OID =~ /^$descrOID\./)
		{
#            print("$OID matches $descrOID\n") if $debug;
            foreach my $k (keys %expectedValues)
            {
			    if ($response->{$OID} =~ /^$k\000?$/)
			    {
                    $OID =~ /\.(\d+)$/; # Got it
                    my $index=$1;
                    $nbIndics++;
                    print "$OID ($response->{$OID}) has to be compared with $expectedValues{$k}\n" if $debug;
				    my $val=$response->{"$valueOID.$index"};
                    return ("UNKNOWN","UNKNOWN: OID $valueOID.$index not found") unless $Primitive->{"checkOIDVal"}->($val);
                    if ($val != $expectedValues{$k})
                    {
                        push(@msg,$response->{$OID}) if $val != $expectedValues{$k};
                        $wrong=1;
                    }
			    }
            }
		}
	}
    return ("CRITICAL","CRITICAL: failed PSU indicator(s): ".join(", ",@msg)) if $wrong;
    return ("UNKNOWN","UNKNOWN: no PSU indicators found") if $nbIndics == 0;
    return ("OK","OK: $nbIndics PSU indicator(s) OK");
},
"statusWithMessage"  => sub {
    # NETWORK-APPLIANCE-MIB::miscGlobalStatus.0 = INTEGER: ok(3)
    # NETWORK-APPLIANCE-MIB::miscGlobalStatusMessage.0 = STRING: "The system's global status is normal. "
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $okValue 		= $parameters->[0];
	my $warnValue		= $parameters->[1];
	my $valueOID	    = (split('/',$variables->[0]))[1];
	my $msgOID	        = (split('/',$variables->[1]))[1];
    my $stateValue = $response->{$valueOID};
    my $msgValue = $response->{$msgOID};
    return ("UNKNOWN","UNKNOWN: OID $valueOID not found") unless $Primitive->{"checkOIDVal"}->($stateValue);
    return ("UNKNOWN","UNKNOWN: OID $msgOID not found") unless $Primitive->{"checkOIDVal"}->($msgValue);
    # TODO: use thresholdIt
    return ("OK","OK: $msgValue") if $stateValue == $okValue;
	return ("WARNING","WARNING: $msgValue") if $stateValue == $warnValue;
    return ("CRITICAL","CRITICAL: $msgValue");
},
"nortelFans8310"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,2,"Fan",$debug);
},
"nortelPsus8310"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,"[2,3]","PSU",$debug);
},
"nortelPsus5510"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $OID		    = (split('/',$variables->[0]))[1];
    	my $raidState = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($raidState);
    	my $i=[
       		{pattern => "5", state => "OK",       message => "OK: Power supply state is optimal"},
       		{pattern => "8", state => "OK",       message => "OK: Power supply is empty"},
       		{pattern => "3", state => "OK",       message => "OK: Power supply is empty"},
        	{pattern => "9", state => "WARNING",  message => "WARNING: Power supply state is degraded"},
        	{pattern => "10", state => "CRITICAL", message => "CRITICAL: Power supply state is failed"},
    	];
    	return $Primitive->{"resultMap"}->($raidState,$i,"UNKNOWN","UNKNOWN: Power supply state is unknown.");
},
"nortelFans5510"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $OID		    = (split('/',$variables->[0]))[1];
    	my $raidState = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($raidState);
    	my $i=[
       		{pattern => "5", state => "OK",       message => "OK: Fan state is optimal"},
       		{pattern => "8", state => "OK",       message => "OK: Fan is empty"},
       		{pattern => "3", state => "OK",       message => "OK: Fan is empty"},
        	{pattern => "9", state => "WARNING",  message => "WARNING: Fan state is degraded"},
        	{pattern => "10", state => "CRITICAL", message => "CRITICAL: Fan state is failed"},
    	];
    	return $Primitive->{"resultMap"}->($raidState,$i,"UNKNOWN","UNKNOWN: Fan state is unknown.");
},
"nortelStack5510"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $OID		    = (split('/',$variables->[0]))[1];
    	my $raidState = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($raidState);
    	my $i=[
       		{pattern => "5", state => "OK",       message => "OK: Stack state is optimal"},
       		{pattern => "8", state => "OK",       message => "OK: Stack is empty"},
        	{pattern => "9", state => "WARNING",  message => "WARNING: Stack state is degraded"},
        	{pattern => "10", state => "CRITICAL", message => "CRITICAL: Stack state is failed"},
    	];
    	return $Primitive->{"resultMap"}->($raidState,$i,"UNKNOWN","UNKNOWN: Stack state is unknown.");
},
"nortelGBic8310"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $OID		    = (split('/',$variables->[0]))[1];
    	my $raidState = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($raidState);
    	my $i=[
       		{pattern => "1", state => "OK",       message => "OK: GBic state is up"},
        	{pattern => "2", state => "WARNING",  message => "WARNING: GBic state is down"},
        	{pattern => "4", state => "CRITICAL", message => "CRITICAL: GBic state is down"},
    	];
    	return $Primitive->{"resultMap"}->($raidState,$i,"UNKNOWN","UNKNOWN: GBic state is unknown.");
},
"nortelRcCards8310"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $descrOID		= (split('/',$variables->[0]))[1];
	my $stateOID		= (split('/',$variables->[1]))[1];
    return $Primitive->{"genericHW"}->($response,$descrOID,$stateOID,"[1,5]","RC Cards",$debug);
},
"packeteerFans"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $OID		    = (split('/',$variables->[0]))[1];
    	my $raidState = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($raidState);
    	my $i=[
       		{pattern => "1", state => "OK",       message => "OK: Fan state is optimal"},
       		{pattern => "3", state => "OK",       message => "OK: Fan is empty"},
        	{pattern => "2", state => "CRITICAL", message => "CRITICAL: Fan state is failed"},
    	];
    	return $Primitive->{"resultMap"}->($raidState,$i,"UNKNOWN","UNKNOWN: Fan state is unknown.");
},
"packeteerPsus"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $OID		    = (split('/',$variables->[0]))[1];
    	my $raidState = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($raidState);
    	my $i=[
       		{pattern => "1", state => "OK",       message => "OK: Power supply state is optimal"},
       		{pattern => "3", state => "OK",       message => "OK: Power supply is empty"},
        	{pattern => "2", state => "CRITICAL", message => "CRITICAL: Power supply state is failed"},
    	];
    	return $Primitive->{"resultMap"}->($raidState,$i,"UNKNOWN","UNKNOWN: Power supply state is unknown.");
},
"packeteerOS"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $OID		    = (split('/',$variables->[0]))[1];
    	my $raidState = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($raidState);
    	my $i=[
       		{pattern => "1", state => "OK",       message => "OK: Current operational traffic shaping status is optimal"},
        	{pattern => "2", state => "CRITICAL", message => "CRITICAL: Current operational traffic shaping status is failed"},
    	];
    	return $Primitive->{"resultMap"}->($raidState,$i,"UNKNOWN","UNKNOWN: Current operational traffic shaping status is unknown.");
},
"overlandDST"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	my $OID		    = (split('/',$variables->[0]))[1];
    	my $raidState = $response->{$OID};
	return ("UNKNOWN","UNKNOWN: OID $OID not found") unless $Primitive->{"checkOIDVal"}->($raidState);
    	my $i=[
       		{pattern => "0", state => "OK",       message => "OK: Drive status is optimal"},
       		{pattern => "3", state => "OK",       message => "OK: Drive status is not installed"},
       		{pattern => "4", state => "OK",       message => "OK: Drive status is not inserted"},
        	{pattern => "1", state => "CRITICAL", message => "CRITICAL: Drive status is initialized with errors"},
        	{pattern => "2", state => "CRITICAL", message => "CRITICAL: Drive status is not initialized"},
    	];
    	return $Primitive->{"resultMap"}->($raidState,$i,"UNKNOWN","UNKNOWN: Power supply state is unknown.");
},
### Metrologie
"m_table"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $name	= $parameters->[0];
	my $OID	    = (split('/',$variables->[0]))[1];
	my $descrOID	= (split('/',$variables->[1]))[1];

	# Get the index
	my $index = $Primitive->{"lookup"}->($response,$descrOID,$name);
	return ("UNKNOWN","U") if ($index == -1);
    my $value=$response->{"$OID.$index"};
	return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($value);
	return ('OK', $value);
},
"m_table_add"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $name	= $parameters->[0];
	my $OID	    = (split('/',$variables->[0]))[1];
	my $descrOID	= (split('/',$variables->[1]))[1];

	# Get the indexes
	my @indexes = $Primitive->{"lookupMultiple"}->($response,$descrOID,$name);
	return ("UNKNOWN","U") if ($#indexes == -1);
    my $total=0;
    my $value;
	foreach my $index (@indexes)
	{
        $value=$response->{"$OID.$index"};
        return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($value);
        $total += $value;
    }
	return ('OK', $total);
},
"m_table_mult"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $name	= $parameters->[0];
	my $val1OID	    = (split('/',$variables->[0]))[1];
	my $val2OID	    = (split('/',$variables->[1]))[1];
	my $descrOID	= (split('/',$variables->[2]))[1];

	# Get the indexes
	my @indexes = $Primitive->{"lookupMultiple"}->($response,$descrOID,$name);
	return ("UNKNOWN","U") if ($#indexes == -1);
    my $total=0;
    my $val1;
    my $val2;
	foreach my $index (@indexes)
	{
        $val1=$response->{"$val1OID.$index"};
        $val2=$response->{"$val2OID.$index"};
        return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($val1);
        return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($val2);
        $total += $val1 * $val2;
    }
	return ('OK', $total);
},
"percentage"			=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $OID		= (split('/',$variables->[0]))[1];
	return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($response->{$OID});
	return ('OK',$response->{$OID}/100);
},
"percentage2values"                    => sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $OID1	= (split('/',$variables->[0]))[1];
	my $OID2	= (split('/',$variables->[1]))[1];
	return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($response->{$OID1});
	return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($response->{$OID2});
	return ('OK',$response->{$OID1}/$response->{$OID2}*100);
},
"directValue"			=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $OID		= (split('/',$variables->[0]))[1];
	return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($response->{$OID});
	return ('OK',$response->{$OID});
},
"m_mult"	=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $OID1		= (split('/',$variables->[0]))[1];
	my $OID2	    = (split('/',$variables->[1]))[1];
	my $val1	    = $response->{$OID1};
	my $val2	    = $response->{$OID2};

	return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($val1);
	return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($val2);
	return ("OK",$val1*$val2);
},
"m_sysUpTime"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;
	
	my $sysUpTimeOID	= (split('/',$variables->[0]))[1];
	my $timestamp		= 0;
	my $sysUpTime		= $response->{$sysUpTimeOID};
	return ("UNKNOWN","U") unless $Primitive->{"checkOIDVal"}->($sysUpTime);

	if ($timestamp = $Primitive->{"date2Time"}->($sysUpTime))
	{
		return ('OK',"$timestamp");
	}
	return ('UNKNOWN', "U");
},
"m_walk_grep_count"		=> sub {
	my ($parameters, $variables, $response, $debug, $Primitive)=@_;

	my $pattern		= $parameters->[0];
	my $walk		= (split('/',$variables->[0]))[1];

	my $value=0;
	# Get the ifIndex
	foreach my $OID (keys %{$response})
	{
		if ($OID =~ /^$walk\./)
		{
			if ($response->{$OID} =~ /^$pattern\000?$/)
			{
				$value++;
			}
		}
	}
	return ("OK", $value);
},
);
1;
