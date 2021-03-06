#!/usr/bin/python

import os
import re
import sys
import signal
import argparse
import subprocess
from pull import PULL
from tabulate import tabulate
from wireless import SNIFFER
from wireless import CAPTURE
from wireless import PMKID
from wireless import HKCRACK
from scapy.utils import rdpcap


DEFAULTHANDLER = signal.getsignal(signal.SIGINT)

class SIGNALER:

	def changer(self):
		signal.signal(signal.SIGINT, self.put_exit)

	def origanl(self):
		global DEFAULTHANDLER

		signal.signal(signal.SIGINT, DEFAULTHANDLER)

	def put_exit(self, sig, fr):
		pull.halt(
			"Received CTRL + C! Exiting Now!",
			True,
			"\r",
			pull.RED
		)

############################################
################# SLAB A ###################
############################################

class SLAB_A:

	def __init__(self, prs):
		self.verbose   = prs.verbose
		self.interface = prs.interface
		self.channels  = prs.channels
		self.essids    = prs.essids
		self.aps       = prs.aps
		self.stations  = prs.stations
		self.filters   = prs.filters
		self.write     = prs.write
		self.packets   = prs.packets
		self.code      = prs.code
		self.delay     = prs.delay

	def sniff(self):
		sniffer = SNIFFER(
			self.interface,
			self.channels,
			self.essids,
			self.aps,
			self.stations,
			self.filters,
			pull,
			self.verbose
		)

		sniffer.sniff()
		aps = sniffer._SNIFFER__ACCESSPOINTS
		return aps

	def pull_aps(self, aps):
		headers = [pull.BOLD + '#', 'BSSID', 'PWR', 'CH', 'ENC', 'CIPHER', 'AUTH', 'DEV', 'ESSID', 'STA\'S' + pull.END] if self.verbose else \
					[pull.BOLD + '#', 'BSSID', 'PWR', 'CH', 'ENC', 'CIPHER', 'AUTH', 'ESSID', 'STA\'S' + pull.END]
		rows = []
		for ap in list(aps.keys()):
			if self.verbose:
				rows.append([
						list(aps.keys()).index(ap),
						pull.DARKCYAN + aps[ ap ][ 'bssid' ].upper() + pull.END,
						pull.RED + str(aps[ ap ][ 'power' ]) + pull.END,
						aps[ ap ][ 'channel' ],
						pull.DARKCYAN + aps[ ap ][ 'encryption' ] + pull.END,
						pull.YELLOW + aps[ ap ][ 'cipher' ] + pull.END,
						pull.YELLOW +  aps[ ap ][ 'auth' ] + pull.END,
						aps[ ap ][ 'device' ],
						pull.GREEN + aps[ ap ][ 'essid' ] + pull.GREEN,
						pull.RED + str(len(aps[ ap ][ 'stations' ])) + pull.END
					])
			else:
				rows.append([
						list(aps.keys()).index(ap),
						pull.DARKCYAN + aps[ ap ][ 'bssid' ].upper() + pull.END,
						pull.RED + str(aps[ ap ][ 'power' ]) + pull.END,
						aps[ ap ][ 'channel' ],
						pull.DARKCYAN + aps[ ap ][ 'encryption' ] + pull.END,
						pull.YELLOW + aps[ ap ][ 'cipher' ] + pull.END,
						pull.YELLOW +  aps[ ap ][ 'auth' ] + pull.END,
						pull.GREEN + aps[ ap ][ 'essid' ] + pull.GREEN,
						pull.RED + str(len(aps[ ap ][ 'stations' ])) + pull.END
					])
		towrite = tabulate(rows, headers=headers) + "\n"
		pull.linebreak()
		pull.write(towrite)
		pull.linebreak()

	def extract(self, aps):
		alist = tuple(range(0, len(aps)))
		alist = [str(it) for it in alist]
		retval = int(pull.input( "?", "Enter Your Target Number: ", alist, pull.BLUE ))
		tgt   = aps.get( list(aps.keys())[ retval ] )
		return tgt

	def loop(self, tgt):
		bssid = tgt.get('bssid')
		essid = tgt.get('essid')
		channel = tgt.get('channel')
		power = tgt.get('power')
		device = tgt.get('device')
		encryption = tgt.get('encryption')
		cipher= tgt.get('cipher')
		auth  = tgt.get('auth')
		stations = tgt.get('stations')

		pull.print(
			"*",
			"TARGET BSS [{bss}] ESS [{ess}] CH [{ch}] PWR [{power}]".format(
				bss=pull.DARKCYAN + bssid.upper() + pull.END,
				ess=pull.YELLOW + essid + pull.END,
				ch =pull.RED + str(channel) + pull.END,
				power=pull.RED  + str(power)  + pull.END
			),
			pull.YELLOW
		)

		pull.print(
			"*",
			"TARGET SEC [{enc}] CPR [{cipher}] AUTH [{auth}] PWR [{stations}]".format(
				enc=pull.DARKCYAN + encryption + pull.END,
				cipher=pull.YELLOW + cipher + pull.END,
				auth =pull.RED + auth + pull.END,
				stations=pull.RED  + str(len(stations)) + pull.END
			),
			pull.YELLOW
		)

		pull.print(
			"-", "Stations Discovered ->", pull.DARKCYAN
		)

		for station in stations:
			pull.indent("-->", station.upper() + " (" + pull.DARKCYAN + pull.get_mac(station) + pull.END + ")", pull.YELLOW)

	def capture(self, tgt):
		bssid = tgt.get('bssid')
		essid = tgt.get('essid')
		channel = tgt.get('channel')
		power = tgt.get('power')
		device = tgt.get('device')
		encryption = tgt.get('encryption')
		cipher= tgt.get('cipher')
		auth  = tgt.get('auth')
		beacon = tgt.get('beacon')
		stations = tgt.get('stations')

		if len(stations) == 0:
			pull.halt("Found No Stations for This Target. Make a Rescan!", True, pull.RED)

		pull.print(
				"^",
				"Engaging with the target...",
				pull.GREEN
			)

		capture = CAPTURE(self.interface, bssid, essid, channel, power, device, encryption, cipher, auth, beacon, stations, self.write, self.packets, self.code, self.delay)
		capture.channeler()

		pull.print(
			"^",
			"Listening to Handshakes ...",
			pull.BLUE
		)

		capture.crater()
		capture.engage()

	def engage(self):
		pull.print(
			"*",
			"IFACE: [{iface}] CHANNELS [{channels}] OPUT [{output}]".format(
				iface=pull.DARKCYAN+self.interface+pull.END,
				channels=pull.DARKCYAN+str(len(self.channels))+pull.END,
				output=pull.DARKCYAN+"YES"+pull.END
			),
			pull.YELLOW
		)
		pull.print(
			"^",
			"Starting Sniffer. Press CTRL+C to Stop",
			pull.GREEN
		)

		aps = self.sniff()
		signal = SIGNALER()
		signal.changer()
		self.pull_aps( aps )
		tgt = self.extract(aps)
		self.loop( tgt )
		signal.origanl()
		del signal
		self.capture( tgt )


############################################
################# SLAB B ###################
############################################

class SLAB_B:

	def __init__(self, prs):
		self.verbose   = prs.verbose
		self.interface = prs.interface
		self.channels  = prs.channels
		self.essids    = prs.essids
		self.aps       = prs.aps
		self.stations  = prs.stations
		self.filters   = prs.filters
		self.write     = prs.write
		self.pauth     = prs.pauth
		self.passo     = prs.passo
		self.dauth     = prs.dauth
		self.dasso     = prs.dasso

	def sniff(self):
		sniffer = SNIFFER(
			self.interface,
			self.channels,
			self.essids,
			self.aps,
			self.stations,
			self.filters,
			pull,
			self.verbose
		)

		sniffer.sniff()
		aps = sniffer._SNIFFER__ACCESSPOINTS
		return aps

	def extract(self, aps):
		alist = tuple(range(0, len(aps)))
		alist = [str(it) for it in alist]
		retval = int(pull.input( "?", "Enter Your Target Number: ", alist, pull.BLUE ))
		tgt   = aps.get( list(aps.keys())[ retval ] )
		return tgt

	def pull_aps(self, aps):
		headers = [pull.BOLD + '#', 'BSSID', 'PWR', 'CH', 'ENC', 'CIPHER', 'AUTH', 'DEV', 'ESSID', 'STA\'S' + pull.END] if self.verbose else \
					[pull.BOLD + '#', 'BSSID', 'PWR', 'CH', 'ENC', 'CIPHER', 'AUTH', 'ESSID', 'STA\'S' + pull.END]
		rows = []
		for ap in list(aps.keys()):
			if self.verbose:
				rows.append([
						list(aps.keys()).index(ap),
						pull.DARKCYAN + aps[ ap ][ 'bssid' ].upper() + pull.END,
						pull.RED + str(aps[ ap ][ 'power' ]) + pull.END,
						aps[ ap ][ 'channel' ],
						pull.DARKCYAN + aps[ ap ][ 'encryption' ] + pull.END,
						pull.YELLOW + aps[ ap ][ 'cipher' ] + pull.END,
						pull.YELLOW +  aps[ ap ][ 'auth' ] + pull.END,
						aps[ ap ][ 'device' ],
						pull.GREEN + aps[ ap ][ 'essid' ] + pull.GREEN,
						pull.RED + str(len(aps[ ap ][ 'stations' ])) + pull.END
					])
			else:
				rows.append([
						list(aps.keys()).index(ap),
						pull.DARKCYAN + aps[ ap ][ 'bssid' ].upper() + pull.END,
						pull.RED + str(aps[ ap ][ 'power' ]) + pull.END,
						aps[ ap ][ 'channel' ],
						pull.DARKCYAN + aps[ ap ][ 'encryption' ] + pull.END,
						pull.YELLOW + aps[ ap ][ 'cipher' ] + pull.END,
						pull.YELLOW +  aps[ ap ][ 'auth' ] + pull.END,
						pull.GREEN + aps[ ap ][ 'essid' ] + pull.GREEN,
						pull.RED + str(len(aps[ ap ][ 'stations' ])) + pull.END
					])
		towrite = tabulate(rows, headers=headers) + "\n"
		pull.linebreak()
		pull.write(towrite)
		pull.linebreak()

	def loop(self, tgt):
		bssid = tgt.get('bssid')
		essid = tgt.get('essid')
		channel = tgt.get('channel')
		power = tgt.get('power')
		device = tgt.get('device')
		encryption = tgt.get('encryption')
		cipher= tgt.get('cipher')
		auth  = tgt.get('auth')
		stations = tgt.get('stations')

		pull.print(
			"*",
			"TARGET BSS [{bss}] ESS [{ess}] CH [{ch}] PWR [{power}]".format(
				bss=pull.DARKCYAN + bssid.upper() + pull.END,
				ess=pull.YELLOW + essid + pull.END,
				ch =pull.RED + str(channel) + pull.END,
				power=pull.RED  + str(power)  + pull.END
			),
			pull.YELLOW
		)

		pull.print(
			"*",
			"TARGET SEC [{enc}] CPR [{cipher}] AUTH [{auth}] PWR [{stations}]".format(
				enc=pull.DARKCYAN + encryption + pull.END,
				cipher=pull.YELLOW + cipher + pull.END,
				auth =pull.RED + auth + pull.END,
				stations=pull.RED  + str(len(stations)) + pull.END
			),
			pull.YELLOW
		)

	def fire(self, tgt):
		bssid = tgt.get('bssid')
		essid = tgt.get('essid')
		channel = tgt.get('channel')
		power = tgt.get('power')
		device = tgt.get('device')
		encryption = tgt.get('encryption')
		cipher= tgt.get('cipher')
		auth  = tgt.get('auth')
		beacon = tgt.get('beacon')
		stations = tgt.get('stations')

		pull.print(
				"^",
				"Engaging with the target...",
				pull.GREEN
			)

		pmkid = PMKID(
						self.interface, bssid, essid, channel, power, device, encryption, cipher, auth, beacon, stations,
						self.write, self.pauth, self.passo, self.dauth, self.dasso
					)

		pmkid.channeler()
		pmkid.engage()

	def engage(self):
		pull.print(
			"*",
			"IFACE: [{iface}] CHANNELS [{channels}] OPUT [{output}]".format(
				iface=pull.DARKCYAN+self.interface+pull.END,
				channels=pull.DARKCYAN+str(len(self.channels))+pull.END,
				output=pull.DARKCYAN+"YES"+pull.END
			),
			pull.YELLOW
		)
		pull.print(
			"^",
			"Starting Sniffer. Press CTRL+C to Stop",
			pull.GREEN
		)

		aps = self.sniff()
		self.pull_aps( aps )
		signal = SIGNALER()
		signal.changer()
		tgt = self.extract(aps)
		self.loop( tgt )
		self.fire( tgt )

#############################################
############## SLAB C #######################
#############################################

class SLAB_C:

	def __init__(self, prs):
		self.packets = prs.packets
		self.passes  = prs.passes
		self.defer   = prs.defer
		self.store   = prs.store
		self.essid   = prs.essid
		self.crack   = HKCRACK(self.packets, self.passes, self.defer, self.store, self.essid)

	def validate(self):
		pkts = self.crack.validate()

		if pkts:
			if self.crack.essid:
				self.crack.count_shakes()
			else:
				pull.halt(
				"The Provided Capture File doesn't Contain any Beacon Frame or ESSID!",
					True, 
					pull.RED
				)	
		else:
			pull.halt(
				"The Provided Capture File doesn't Contain any Valid Handshake!",
				True, 
				pull.RED
			)

	def engage(self):
		pull.print(
			"*",
			"Crack Mode [{mode}] Packets [{capture}]".format(
				mode=pull.YELLOW+"EAPOL 4 Handshakes"+pull.END,
				capture=pull.RED+str(len(self.packets))+pull.END,
			),
			pull.YELLOW
		)
		pull.print(
			"*",
			"Captured Passes [{passes}] Store [{store}]".format(
				passes=pull.DARKCYAN+str(len(self.passes))+pull.END,
				store=pull.DARKCYAN+("True" if self.store else "False")+pull.END
			),
			pull.YELLOW
		)
		
		self.validate()
		self.crack.engage()

#############################################
############## HANDLER ######################
#############################################


class HANDLER:

	def __init__(self, mode, prs):
		self.mode   = mode
		self.parser = prs

	def engage(self):
		if self.mode == 1:
			slab = SLAB_A(self.parser)
		elif self.mode == 2:
			slab = SLAB_B(self.parser)
		elif self.mode == 3:
			slab = SLAB_C(self.parser)
			
		slab.engage()

class PARSER:

	def __init__(self, prs):
		# Mode Detector
		self.help      = self.helper(prs.help, prs.mode)
		self.mode      = self.mode(prs.mode)

		# Filters
		self.verbose   = prs.verbose

		if self.mode == 1:
			self.world     = prs.world
			self.interface = self.interface(prs.interface)
			self.channels  = self.channels(prs.channels)
			self.essids    = self.form_essids(prs.essids)
			self.aps       = self.form_macs(prs.aps)
			self.stations  = self.form_macs(prs.stations)
			self.filters   = self.form_macs(prs.filters)
			self.output    = self.output(prs.output)
			self.packets   = prs.packets if prs.packets >= 1 else pull.halt("Invalid Number of Packets Specified!", True, pull.RED)
			self.code      = prs.code    if prs.code    >= 1 else pull.halt("Invalid Code Given!", True, pull.RED)
			self.delay     = prs.delay   if prs.delay   >= 0 else pull.halt("Invalid Delay Specified!", True, pull.RED)

		elif self.mode == 2:
			self.world     = prs.world
			self.interface = self.interface(prs.interface)
			self.channels  = self.channels(prs.channels)
			self.essids    = self.form_essids(prs.essids)
			self.aps       = self.form_macs(prs.aps)
			self.stations  = self.form_macs(prs.stations)
			self.filters   = self.form_macs(prs.filters)
			self.output    = self.pmkid(prs.pmkid)
			self.pauth     = prs.pauth   if prs.pauth >= 1 else pull.halt("Invalid Number of Authentication Packets!", True, pull.RED)
			self.passo     = prs.passo   if prs.passo >= 1 else pull.halt("Invalid Number of Association Packets!", True, pull.RED)
			self.dauth     = prs.dauth   if prs.dauth >= 0 else pull.halt("Invalid Authentication Delay Specified!", True, pull.RED)
			self.dasso     = prs.dasso   if prs.dasso >= 0 else pull.halt("Invalid Assocaition Delay Specified!", True, pull.RED)

		elif self.mode == 3:
			self.packets   = self.packets(prs.read)
			self.passes    = self.passes(prs.wordlist, prs.mask)
			self.defer     = prs.defer if prs.defer >= 0 else pull.halt("Invalid Defer Time Provided!", True, pull.RED)
			self.store     = self.store(prs.store)
			self.essid     = prs.essid if prs.essid else None

	def packets(self, fl):
		if fl:
			pkts = rdpcap(fl)
			return pkts
		else:
			pull.halt("Handshake File Not Supplied!", True, pull.RED)

	def passes(self, wd, mk):
		if not wd and not mk:
			pull.halt("Wordlist or Mask Required to Perform the Attack!", True, pull.RED)
		else:
			if mk:
				return mk
			else:
				fl    = open(wd)
				lines = fl.read().splitlines()

				return lines

	def store(self, fl):
		if fl:
			return fl
		else:
			pull.halt("Ouptut File Not Provided! No Output Will be Produced!", False, pull.RED)
			return None

	def helper(self, hl, md):
		if hl:
			if not md:
				pull.help()
			else:
				if md == 1:
					pull.helpa()
				elif md == 2:
					pull.helpb()
				elif md == 3:
					pull.helpc()

	def mode(self, md):
		amodes = (1, 2, 3)
		if md in amodes:
			return md
		else:
			pull.halt("Invalid Mode Supplied. ", True, pull.RED)

	def pmkid(self, fl):
		if fl:
			return fl
		else:
			pull.halt("Capture File Not Provided. No PMKID will be Stored!", False, pull.RED)

	def output(self, fl):
		if fl:
			return fl
		else:
			pull.halt("Capture File Not Provided. No Output will be Stored!", False, pull.RED)

	def channels(self, ch):
		retval = list(range(1,15)) if self.world else list(range(1,12))
		if ch:
			if ch in retval:
				return [ch]
			else:
				pull.halt("Invalid Channel Given.", True, pull.RED)
		else:
			return retval

	def form_essids(self, essids):
		retval = []
		if essids:
			toloop = essids.split(",")
			for essid in toloop:
				retval.append(essid)

		return retval

	def form_macs(self, bssids):
		retval = []
		if bssids:
			toloop = bssids.split(",")
			for bssid in toloop:
				if re.search(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", bssid):
					retval.append(bssid.lower())

		return retval

	def interface(self, iface):
		def getNICnames():
			ifaces = []
			dev = open('/proc/net/dev', 'r')
			data = dev.read()
			for n in re.findall('[a-zA-Z0-9]+:', data):
				ifaces.append(n.rstrip(":"))
			return ifaces

		def confirmMon(iface):
			co = subprocess.Popen(['iwconfig', iface], stdout=subprocess.PIPE)
			data = co.communicate()[0].decode()
			card = re.findall('Mode:[A-Za-z]+', data)[0]	
			if "Monitor" in card:
				return True
			else:
				return False

		if iface:
			ifaces = getNICnames()
			if iface in ifaces:
				if confirmMon(iface):
					return iface
				else:
					pull.halt("Interface Not In Monitor Mode [%s]" % (pull.RED + iface + pull.END), True, pull.RED)
			else:
				pull.halt("Interface Not Found. [%s]" % (pull.RED + iface + pull.END), True, pull.RED)
		else:
			pull.halt("Interface Not Provided. Specify an Interface!", True, pull.RED)

class PARSERX:

	def __init__(self, opts):
		self.mode = self.mode(opts.mode, opts.help)
		self.help = self.help(opts.help)

	def help(self, hp):
		if hp:
			if self.mode == 1:
				pull.helpa()
			elif self.mode == 2:
				pull.helpb()
			elif self.mode == 3:
				pull.helpc()

	def mode(self, md, hp):
		if md:
			if md in (1, 2, 3):
				return md
			else:
				pull.halt(
					"Invalid Mode Supplied!",
					True,
					pull.RED
				)
		else:
			if hp:
				pull.help()
			else:
				pull.halt(
					"No Mode Supplied! Required Argument.",
					True,
					pull.RED
				)

class PARSERA:

	def __init__(self, opts):
		self.world     = opts.world
		self.interface = self.interface(opts.interface)
		self.channels  = self.channels(opts.channels)
		self.essids    = self.form_essids(opts.essids)
		self.aps       = self.form_macs(opts.aps)
		self.stations  = self.form_macs(opts.stations)
		self.filters   = self.form_macs(opts.filters)
		self.write     = self.write(opts.write)
		self.packets   = opts.packets if opts.packets >= 1 else pull.halt("Invalid Number of Packets Specified!", True, pull.RED)
		self.code      = opts.code    if opts.code    >= 1 else pull.halt("Invalid Code Given!", True, pull.RED)
		self.delay     = opts.delay   if opts.delay   >= 0 else pull.halt("Invalid Delay Specified!", True, pull.RED)
		self.verbose   = opts.verbose

	def write(self, wr):
		if wr:
			return wr
		else:
			pull.halt("Capture File Not Provided. No Output will be Stored!", False, pull.RED)

	def form_macs(self, bssids):
		retval = []
		if bssids:
			toloop = bssids.split(",")
			for bssid in toloop:
				if re.search(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", bssid):
					retval.append(bssid.lower())

		return retval

	def form_essids(self, essids):
		retval = []
		if essids:
			toloop = essids.split(",")
			for essid in toloop:
				retval.append(essid)

		return retval

	def channels(self, ch):
		retval = list(range(1,15)) if self.world else list(range(1,12))
		if ch:
			if ch in retval:
				return [ch]
			else:
				pull.halt("Invalid Channel Given.", True, pull.RED)
		else:
			return retval

	def interface(self, iface):
		def getNICnames():
			ifaces = []
			dev = open('/proc/net/dev', 'r')
			data = dev.read()
			for n in re.findall('[a-zA-Z0-9]+:', data):
				ifaces.append(n.rstrip(":"))
			return ifaces

		def confirmMon(iface):
			co = subprocess.Popen(['iwconfig', iface], stdout=subprocess.PIPE)
			data = co.communicate()[0].decode()
			card = re.findall('Mode:[A-Za-z]+', data)[0]	
			if "Monitor" in card:
				return True
			else:
				return False

		if iface:
			ifaces = getNICnames()
			if iface in ifaces:
				if confirmMon(iface):
					return iface
				else:
					pull.halt("Interface Not In Monitor Mode [%s]" % (pull.RED + iface + pull.END), True, pull.RED)
			else:
				pull.halt("Interface Not Found. [%s]" % (pull.RED + iface + pull.END), True, pull.RED)
		else:
			pull.halt("Interface Not Provided. Specify an Interface!", True, pull.RED)

class PARSERB:

	def __init__(self, opts):
		self.world     = opts.world
		self.interface = self.interface(opts.interface)
		self.channels  = self.channels(opts.channels)
		self.essids    = self.form_essids(opts.essids)
		self.aps       = self.form_macs(opts.aps)
		self.stations  = self.form_macs(opts.stations)
		self.filters   = self.form_macs(opts.filters)
		self.write     = self.write(opts.write)
		self.pauth     = opts.pauth if opts.pauth > 0 else pull.halt("Invalid Number of Authentication Packets Specified!", True, pull.RED)
		self.passo     = opts.passo if opts.passo > 0 else pull.halt("Invalid Number of Association Packets Specified!", True, pull.RED)
		self.dauth     = opts.dauth if opts.dauth >= 0 else pull.halt("Invalid Delay Specified for Authentication Packets!", True, pull.RED)
		self.dasso     = opts.dasso if opts.dasso >= 0 else pull.halt("Invalid Delay Specified for Association Packets!", True, pull.RED)
		self.verbose   = opts.verbose

	def write(self, wr):
		if wr:
			if wr.endswith(".pmkid"):
				return wr
			elif wr.endswith("."):
				return (wr + "pmkid")
			else:
				return (wr + ".pmkid")
		else:
			return False

	def form_macs(self, bssids):
		retval = []
		if bssids:
			toloop = bssids.split(",")
			for bssid in toloop:
				if re.search(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", bssid):
					retval.append(bssid.lower())

		return retval

	def form_essids(self, essids):
		retval = []
		if essids:
			toloop = essids.split(",")
			for essid in toloop:
				retval.append(essid)

		return retval

	def channels(self, ch):
		retval = list(range(1,15)) if self.world else list(range(1,12))
		if ch:
			if ch in retval:
				return [ch]
			else:
				pull.halt("Invalid Channel Given.", True, pull.RED)
		else:
			return retval

	def interface(self, iface):
		def getNICnames():
			ifaces = []
			dev = open('/proc/net/dev', 'r')
			data = dev.read()
			for n in re.findall('[a-zA-Z0-9]+:', data):
				ifaces.append(n.rstrip(":"))
			return ifaces

		def confirmMon(iface):
			co = subprocess.Popen(['iwconfig', iface], stdout=subprocess.PIPE)
			data = co.communicate()[0].decode()
			card = re.findall('Mode:[A-Za-z]+', data)[0]	
			if "Monitor" in card:
				return True
			else:
				return False

		if iface:
			ifaces = getNICnames()
			if iface in ifaces:
				if confirmMon(iface):
					return iface
				else:
					pull.halt("Interface Not In Monitor Mode [%s]" % (pull.RED + iface + pull.END), True, pull.RED)
			else:
				pull.halt("Interface Not Found. [%s]" % (pull.RED + iface + pull.END), True, pull.RED)
		else:
			pull.halt("Interface Not Provided. Specify an Interface!", True, pull.RED)

def main():
	parser = argparse.ArgumentParser(add_help=False)

	parser.add_argument('-h', '--help', dest="help", default=False, action="store_true")
	parser.add_argument('-m', '--mode', dest="mode", default=0    , type=int)

	(opts, args) = parser.parse_known_args()
	parser = PARSERX(opts)

	if parser.mode == 1:
		parsera = argparse.ArgumentParser(add_help=False)

		parsera.add_argument('-i', '--interface'    , dest="interface", default=""   , type=str  )
		parsera.add_argument('-c', '--channel'      , dest="channels" , default=0    , type=int  )
		parsera.add_argument('-e', '--essids'       , dest="essids"   , default=""   , type=str  )
		parsera.add_argument('-a', '--accesspoints' , dest="aps"      , default=""   , type=str  )
		parsera.add_argument('-s', '--stations'     , dest="stations" , default=""   , type=str  )
		parsera.add_argument('-f', '--filters'      , dest="filters"  , default=""   , type=str  )
		parsera.add_argument('-w', '--write'        , dest="write"    , default=""   , type=str  )
		parsera.add_argument('-p', '--packets'      , dest="packets"  , default=3    , type=int  )
		parsera.add_argument(      '--code'         , dest="code"     , default=7    , type=int  )
		parsera.add_argument(      '--delay'        , dest="delay"    , default=0.01 , type=float)
		parsera.add_argument(      '--world'        , dest="world"    , default=False, action="store_true")
		parsera.add_argument(      '--verbose'      , dest="verbose"  , default=False, action="store_true")

		(opts, args) = parsera.parse_known_args()
		parsera      = PARSERA(opts)

		pull.print(
			"^",
			"Starting Broot Handshake/Capturer...",
			pull.DARKCYAN
		)

		handler      = HANDLER(parser.mode, parsera)
		handler.engage()

		pull.print(
			"<",
			"Done!",
			"\r", pull.DARKCYAN
		)

	elif parser.mode == 2:
		parserb = argparse.ArgumentParser(add_help=False)

		parserb.add_argument('-i',  '--interface'    , dest="interface", default=""   , type=str  )
		parserb.add_argument('-c',  '--channel'      , dest="channels" , default=0    , type=int  )
		parserb.add_argument('-e',  '--essids'       , dest="essids"   , default=""   , type=str  )
		parserb.add_argument('-a',  '--accesspoints' , dest="aps"      , default=""   , type=str  )
		parserb.add_argument('-s',  '--stations'     , dest="stations" , default=""   , type=str  )
		parserb.add_argument('-f',  '--filters'      , dest="filters"  , default=""   , type=str  )
		parserb.add_argument('-w',  '--write'        , dest="write"    , default=""   , type=str  )
		parserb.add_argument(       '--pkts-auth'    , dest="pauth"    , default=1    , type=int  )
		parserb.add_argument(       '--pkts-asso'    , dest="passo"    , default=1    , type=int  )
		parserb.add_argument(       '--delay-auth'   , dest="dauth"    , default=3    , type=int  )
		parserb.add_argument(       '--delay-asso'   , dest="dasso"    , default=5    , type=int  )
		parserb.add_argument(       '--world'        , dest="world"    , default=False, action="store_true")
		parserb.add_argument(       '--verbose'      , dest="verbose"  , default=False, action="store_true")

		(opts, args) = parserb.parse_known_args()
		parserb      = PARSERB(opts)

		pull.print(
			"^",
			"Starting Broot PMKID/Capturer...",
			pull.DARKCYAN
		)

		handler      = HANDLER(parser.mode, parserb)
		handler.engage()

		pull.print(
			"<",
			"Done!",
			"\r", pull.DARKCYAN
		)

	elif parser.mode == 3:
		parserc = argparse.ArgumentParser(add_help=False)

		parserc.add_argument('-r', '--read'         , dest="read"     , default="", type=str )
		parserc.add_argument('-w', '--wordlist'     , dest="wordlist" , default="", type=str )
		parserc.add_argument('-p', '--pattern'      , dest="pattern"  , default="", type=str )
		parserc.add_argument('-d', '--defer'        , dest="defer"    , default=0 , type=int )
		parserc.add_argument('-e', '--essid'        , dest="essid"    , default="", type=str )
		parserc.add_argument('-w', '--write'        , dest="write"    , default="", type=str )
		parserc.add_argument(      '--verbose'      , dest="verbose"   , default=False, action="store_true")

		(opts, args) = parserc.parse_known_args()
		parserc      = PARSERC(opts)

		pull.print(
			"^",
			"Starting Broot Engine [EAPOLS]...",
			pull.DARKCYAN
		)

		handler = HANDLER(parser.mode, parserc)
		handler.engage()

		pull.print(
			"<",
			"Done!",
			"\r", pull.DARKCYAN
		)

if __name__ == "__main__":
	pull = PULL()
	main()