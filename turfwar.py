#!/usr/bin/env python3
import asyncio
import pickle
from voip import runVoipClient, loadWAVtoPCM, TTStoPCM

def save(var):
	exec('with open("'+var+'''.pkl", "wb") as file:
		pickle.dump('''+var+', file)')

def load (var):
	exec('''try:
	with open("'''+var+'''.pkl", 'rb') as file:
		'''+var+''' = pickle.load(file)
except (FileNotFoundError, pickle.UnpicklingError) as e:
	print("couldn't load saved variable'''+var+''':", e)
	'''+var+''' = {}''')

try:
	with open("turf.pkl", 'rb') as file:
		turf = pickle.load(file)
except (FileNotFoundError, pickle.UnpicklingError) as e:
	print("couldn't load saved tree:", e)
	turf = {}

try:
	with open("users.pkl", 'rb') as file:
		users = pickle.load(file)
except (FileNotFoundError, pickle.UnpicklingError) as e:
	print("couldn't load saved tree:", e)
	users = {}

async def handler(call):
	pn=call.getRemoteUri()
	pn=pn[pn.rfind(" <sip:")+6:pn.rfind("@")]
	print(pn)
	pb= call.playPCM(TTStoPCM("Please enter star to contest this phone. Or press pound to sign up or sign in",engine="rhvoice"))
	try:
		key = await asyncio.wait_for(call.getDTMF(filter="#*"),30)
	except TimeoutError:
		key = "Timeout"
	pb.cancel()
	if key =="#":
		if pn in users:
			print("User Account Exists, Sign In Not Implemented")
			return

		while True:
			await call.playPCM(TTStoPCM("Please enter a 4 digit user I D after the beep.",engine="rhvoice"))
			await call.playTone(420, .5)
			try:
				uid = await asyncio.wait_for(call.getDTMF(n=4, filter="1234567890"),60)
			except TimeoutError:
				break

			if uid not in users.values():
				users[pn] = uid
				save("users")
				break

			await call.playPCM(TTStoPCM("I D Already in use, please try a different I D.",engine="rhvoice"))

	if key =="*":
		if pn in turf:
			print("Phone Already controlled by user I D "+" ".join(turf[pn][0])+", capture not implemented")
		else:
			await call.playPCM(TTStoPCM("Phone uncontested",engine="rhvoice"))
			pb= call.playPCM(TTStoPCM("To capture, please enter your I D.", engine = "rhvoice"))
			try:
				uid = await asyncio.wait_for(call.getDTMF(n=4, filter="1234567890"),60)
			except TimeoutError:
				await call.playPCM(TTStoPCM("Capture Timed Out. Goodbye.",engine="rhvoice"))
				return
			pb.cancel()
			if uid not in users.values():
				await call.playPCM(TTStoPCM("No User with that I D. Goodbye.",engine="rhvoice"))
				return
			while True:
				pb= call.playPCM(TTStoPCM("To secure the capture, please enter a 5 digit locking code.", engine = "rhvoice"))
				try:
					code = await asyncio.wait_for(call.getDTMF(n=5, filter="1234567890"),60)
				except TimeoutError:
					await call.playPCM(TTStoPCM("Capture Timed Out. Goodbye.",engine="rhvoice"))
					break
				pb.cancel()
				pb=call.playPCM(TTStoPCM("Locking Code "+" ".join(code)+", press star to confirm or pound to try again.", engine = "rhvoice"))
				try:
					key = await asyncio.wait_for(call.getDTMF(filter="#*"),30)
				except TimeoutError:
					await call.playPCM(TTStoPCM("Capture Timed Out. Goodbye.",engine="rhvoice"))
					break
				pb.cancel()
				if key == "*":
					await call.playPCM(TTStoPCM("Code Confirmed, saving.", engine = "rhvoice"))
					turf[pn]=[uid,code]
					save("turf")
					await call.playPCM(TTStoPCM("Saved, goodbye.", engine = "rhvoice"))
					break

if __name__ == "__main__":
	runVoipClient(handler)
