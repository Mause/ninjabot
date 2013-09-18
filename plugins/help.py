class Plugin:
	def __init__(self, controller, config):
		self.c = controller

	def trigger_help(self, msg):
		"Usage: help [trigger]. Lists avaliable triggers. If trigger is specified, will print help for that trigger (if avaliable)."

		prefix = self.c.command_prefix
		if len(msg.args) == 0:
			self.c.notice(msg.nick, 'Avaliable triggers:')
			self.c.notice(msg.nick, prefix+(', '+prefix).join(sorted(self.c.triggers.keys())))
			self.c.notice(msg.nick, 'For further info, type '+prefix+'help <trigger>')
		else:
			if msg.args[0].lstrip(prefix) in self.c.triggers:
				doc = self.c.triggers[msg.args[0].lstrip(prefix)].__doc__
				if doc:
					self.c.notice(msg.nick, doc)
				else:
					self.non_existent_help(msg)
			else:
				self.non_existent_help(msg)

	def non_existent_help(self, msg):
		self.c.notice(msg.nick, "Either that trigger does not exist, or it has no documentation.")
		

