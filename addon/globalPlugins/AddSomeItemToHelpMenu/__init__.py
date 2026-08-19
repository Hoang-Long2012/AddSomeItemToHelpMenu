# Add some item to help menu
# Copyright (C) 2026 Hoàng Long
# This add-on is licensed under the GPL2 license

# Import necessary libraries
from documentationUtils import reportNoDocumentation
from logHandler import log
import globalPluginHandler
import addonHandler
import globalVars
import ui
import gui
import wx
import os
import urllib3
import markdown

# For translation
addonHandler.initTranslation()

# Define a base globalPlugin return decorator as NVDA running in secure desktop
def disableIfOnSecureDesktop(pluginClass):
	if globalVars.appArgs.secure:
		return globalPluginHandler.GlobalPlugin
	return pluginClass

# Formatter for contributors
def formatContributors(text):
	text = text.replace(
		"https://github.com/nvaccess/nvda/graphs/contributors",
		"<https://github.com/nvaccess/nvda/graphs/contributors>",
	)
	text = text.replace(
		"https://github.com/nvaccess/nvda/blob/master/projectDocs/community/expertsList.md",
		"<https://github.com/nvaccess/nvda/blob/master/projectDocs/community/expertsList.md>",
	)
	contributors = ["# Contributors"]
	list_started = False
	for line in text.splitlines():
		if not line.strip():
			if not list_started:
				list_started = True
				contributors.append("")
			continue
		line = line.strip()
		if list_started:
			contributors.append("- " + line)
		else:
			contributors.append(line)
	return markdown.markdown("\n".join(contributors))

# Define globalPlugin class
@disableIfOnSecureDesktop  # If n v d a is running on a secure desktop returns the base global Plugin class
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		# A Urllib3 pool manager
		self.https = urllib3.PoolManager()
		# NVDA's Help menu object
		self.helpMenu = gui.mainFrame.sysTrayIcon.helpMenu
		# Create items in NVDA's help menu
		self.createMenuItems()

	def createMenuItems(self):
		self.devGuide = None
		self.NVAccessBlog = None
		self.contributors = None
		self.repo = None
		self.donate = None

		# Translators: Label of Developer Guide menu item
		devGuideLabel = _("Developer &Guide")
		if self.helpMenu.FindItem(devGuideLabel) == wx.NOT_FOUND:
			self.devGuide = self.helpMenu.Insert(4, wx.ID_ANY, devGuideLabel)
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.openDevGuide, self.devGuide)

		# Translators: Label of NV Access blog menu item
		NVAccessBlogLabel = _("NV Access &blog")
		if self.helpMenu.FindItem(NVAccessBlogLabel) == wx.NOT_FOUND:
			self.NVAccessBlog = self.helpMenu.Insert(6, wx.ID_ANY, NVAccessBlogLabel)
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.inProcess, self.NVAccessBlog)

		# Translators: Label of Contributors menu item
		contributorsLabel = _("Contribut&ors")
		if self.helpMenu.FindItem(contributorsLabel) == wx.NOT_FOUND:
			self.contributors = self.helpMenu.Insert(11, wx.ID_ANY, contributorsLabel)
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.openContributors, self.contributors)

		# Translators: Label of GitHub repo menu item
		GitHubRepoLabel = _("GitHub &repository")
		if self.helpMenu.FindItem(GitHubRepoLabel) == wx.NOT_FOUND:
			self.repo = self.helpMenu.Insert(12, wx.ID_ANY, GitHubRepoLabel)
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.gitHubRepo, self.repo)

		# Translators: Label of Donate menu item
		DonateLabel = _("&Donate")
		if self.helpMenu.FindItem(DonateLabel) == wx.NOT_FOUND:
			self.donate = self.helpMenu.Insert(13, wx.ID_ANY, DonateLabel)
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.NVDADonate, self.donate)

	def terminate(self, *args, **kwargs):
		self.https.clear()
		# Remove menu items that the add-on created
		if self.devGuide is not None and self.helpMenu.FindItemById(self.devGuide.GetId()):
			self.helpMenu.Delete(self.devGuide)
		if self.NVAccessBlog is not None and self.helpMenu.FindItemById(self.NVAccessBlog.GetId()):
			self.helpMenu.Delete(self.NVAccessBlog)
		if self.contributors is not None and self.helpMenu.FindItemById(self.contributors.GetId()):
			self.helpMenu.Delete(self.contributors)
		if self.repo is not None and self.helpMenu.FindItemById(self.repo.GetId()):
			self.helpMenu.Delete(self.repo)
		if self.donate is not None and self.helpMenu.FindItemById(self.donate.GetId()):
			self.helpMenu.Delete(self.donate)
		super().terminate(*args, **kwargs)

	def openDevGuide(self, event):
		fileName = "developerGuide.html"
		filePath = os.path.join(globalVars.appDir, "documentation", fileName)
		if not os.path.isfile(filePath):
			reportNoDocumentation(fileName, True)
		os.startfile(filePath)

	def openContributors(self, event):
		fileName = "contributors.txt"
		filePath = os.path.join(globalVars.appDir, "documentation", fileName)
		response = None
		try:
			response = self.https.request("GET", f"https://raw.githubusercontent.com/nvaccess/nvda/master/{fileName}", timeout=urllib3.Timeout(connect=2.0, read=10.0))
			if response.status != 200:
				raise urllib3.exceptions.HTTPError(f"HTTP Error: {response.status} {response.reason}")
			old = ""
			if os.path.isfile(filePath):
				with open(filePath, "r", encoding="utf-8-sig") as file:
					old = file.read()
			data = response.data.decode("utf-8-sig")
			if data != old:
				with open(filePath, "w", encoding="utf-8-sig") as file:
					file.write(data)
		except Exception:
			log.exception(f"Cannot update {fileName}")
		finally:
			if response is not None:
				response.release_conn()
		if os.path.isfile(filePath):
			with open(filePath, "r", encoding="utf-8-sig") as file:
				message = formatContributors(file.read())
				ui.browseableMessage(message=message, title=_("NVDA Contributors"), isHtml=True)
				return None
		reportNoDocumentation(fileName, True)

	def gitHubRepo(self, event):
		wx.LaunchDefaultBrowser("https://github.com/nvaccess/nvda")

	def inProcess(self, event):
		wx.LaunchDefaultBrowser("https://www.nvaccess.org/category/in-process/")

	def NVDADonate(self, event):
		wx.LaunchDefaultBrowser(gui.DONATE_URL)