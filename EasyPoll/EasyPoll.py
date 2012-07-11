# -*- coding: utf-8 -*-
"""
EasyPoll: Fully featured Database driven poll macro with permission controlls for voting and poll creation. Google charts for showing poll results.
Description: The purpose of this macro is to provide an easy way to integrate polls in Trac wiki and ticket pages.
Easy poll uses mysql db for storing poll related data and uses google charts to show results of polls.
Features:
1. Response type: You can decide the response type for polls i.e whether you want single response poll(radio button poll) or multiple response poll(checkbox button poll).
2. Google charts type: You can decide which type of chart you want to use for showing results.
3. Poll options: Poll option can be any valid english string or any Ticket number(EasyPoll will fetch summary for ticket id given and use as a option text).
4. Change vote: You can manage whether user can change their vote or not.

License: BSD
Author: Pankaj Meena
Author Email: hi.amigo@gmail.com
Maintained by: hi.amigo@gmail.com

Provide feedback/suggestions/feature request to hi.amigo@gmail.com

"""

import os
import re
import hashlib
import urlparse
import sys
import simplejson as json

reload(sys)
sys.setdefaultencoding('utf-8')

from trac import util
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.wiki.macros import WikiMacroBase
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.web import IRequestHandler
from genshi.template import TemplateLoader
from trac.env import Environment
from trac.wiki.formatter import wiki_to_oneliner
from trac.ticket.model import Ticket
from trac.util import escape
from trac.perm import IPermissionRequestor

class EasyPollMacro(WikiMacroBase):
    """
        EasyPoll: Fully featured Database driven poll plugin with permission controlls for voting and poll creation. Google charts for showing poll results.
        Description: The purpose of this plugin is to provide an easy way to integrate polls in Trac wiki and ticket pages.
        Easy poll uses mysql db for storing poll related data and uses google charts to show results of polls.
        Features:
        1. Response type: You can decide the response type for polls i.e whether you want single response poll(radio button poll) or multiple response poll(checkbox button poll).
        2. Google charts type: You can decide which type of chart you want to use for showing results.
        3. Poll options: Poll option can be any valid english string or any Ticket number(EasyPoll will fetch summary for ticket id given and use as a option text).
        4. Change vote: You can manage whether user can change their vote or not.
        
        Sample Example:
        ------------------------------------------------------------------------
        
        [[EasyPoll( name = my first poll,
                    title = What's your favorite programming language?,
                    response_type = single,
                    options = Python : PHP : JAVA : C : Lisp,
                    user_can_change_vote = false,
                    chart_type = pie
                   )
        ]]
        
        Attributes explanation:
        ------------------------------------------------------------------------
        1. name(required) : name is used as a poll identifier, if you change the name value than it will be treated as new poll.
        Nowhere in the poll the name will be shown. Don't change the name of the poll after poll creation
        2. title(required) : title will be used as a poll title. You can change it whenever you want. Each time the existing poll will be updated.
        3. options(required) : options should be separated by colon (:)
            option can also have Ticket id as their option like
            options = #1 : #2 : #3 In this case the summary will be pulled out from the valid tickets and will be used as option text with ticket link.
        4. response(optional) : reponse can take two values (i) multiple and (ii) single. Default is (ii)single option
            (i) multiple : multiple response type will generate poll with checkboxes, in this case user can choose multiple options.
            (ii) single : single reponse type will generate poll with radio buttons, in this case user can choose only one option
        5. user_can_change_vote(optional) : user_can_change_vote can take two values (i) false and (ii) true. Default is false
            (i) false : once user cast their vote, they cannot change their vote, Poll will be disabled for them, however they can see poll results.
            (ii) true : user can change their vote anytime and many times. Poll will always be enabled for them and they can see poll results.
        6. chart_type(optional) : chart_type can take two values (i) pie and (ii) bar. Default is pie.
            (i) pie : Pie chart will be used to show poll results.
            (ii) bar : Bar chart will be used to show poll results.
            User can see poll results only after casting their vote.
            
        Permissions Explanation:
        ------------------------------------------------------------------------
        1. EASYPOLL_CREATE : User who has EASYPOLL_CREATE or TRAC_ADMIN permission can create easy polls in wiki or ticket page.
        2. EASYPOLL_VOTE : User who has EASYPOLL_VOTE or TRAC_ADMIN permission can vote on easy polls in wiki or ticket page.
        
        Every login user on Trac can see EasyPoll but can vote or create only if user has sufficient permissions.
        
        Limitations:
        ------------------------------------------------------------------------
        1. As of now only supports ascii characters.
        2. Don't use comma(,) while picking easy poll attributes. By design comma(,) is used as a attribute separator
        
    """
     
    implements(ITemplateProvider, IPermissionRequestor)
    
    def expand_macro(self, formatter, name, args):
        req = formatter.req
        
        pollValidTypes = ["single", "multiple"]
        changeVoteValidOptions = ["true", "false"]
        validChartTypes = ["bar", "pie"]
        
        pollType = "single"
        pollOptions = []
        pollName = None
        optionsLabelDict = {}
        optionsLabelDictForGraph = {}
        userCanChangeVote = "false"
        pollIdentifier = None
        chartType = "pie"
        
        args = args.strip()
        splitData = args.split(",")
        if len(splitData) > 0:
            for arg in splitData:
                argSplitData = arg.split("=")
                key = argSplitData[0].strip()
                value = argSplitData[1].strip()
                if key == "response_type":
                    if value in pollValidTypes:
                        pollType = value.strip()
                elif key == "title":
                    pollName = value.strip()
                elif key == "options":
                    tp = value.split(":")
                    updatePollOptions = []
                    optionsLabelDict = {}
                    for op in tp:
                        if len(op.strip()) > 0:
                            tempOp = op.strip()
                            if tempOp.startswith("#"):
                                tempTicketId = tempOp[1:]
                                if tempTicketId.isdigit():
                                    try:
                                        ticketObj = Ticket(self.env, tempTicketId)
                                        if ticketObj is not None and ticketObj.exists:
                                            ticketStr = ticketObj["summary"].strip()
                                            hashOp = self.getStringHash(ticketStr)
                                            updatePollOptions.append(hashOp)
                                            ticketLbl = ticketStr + ' Link: #%i' % int(tempTicketId)
                                            optionsLabelDict[hashOp] = escape(wiki_to_oneliner(ticketLbl, self.env, req=req))
                                            optionsLabelDictForGraph[hashOp] = escape(ticketLbl)
                                    except:
                                        pass
                            else:
                                hashOp = self.getStringHash(tempOp)
                                updatePollOptions.append(hashOp)
                                optionsLabelDict[hashOp] = escape(wiki_to_oneliner((tempOp), self.env, req=req))
                                optionsLabelDictForGraph[hashOp] = escape(tempOp)
                    pollOptions = updatePollOptions
                elif key == "user_can_change_vote":
                    if value in changeVoteValidOptions:
                        userCanChangeVote = value
                elif key == "chart_type":
                    if value in validChartTypes:
                        chartType = value
                elif key == "name":
                    pollIdentifier = value
                    
        if pollIdentifier is not None and pollName is not None and len(pollOptions) > 0:
            html = self.getPollHTML(req, pollIdentifier, pollName, pollType, pollOptions, userCanChangeVote, chartType, optionsLabelDict, optionsLabelDictForGraph)
            return html
        else:
            return self.getMsgTemplate('Information given for poll is insufficient/improper')
        
    def getPollHTML(self, req, pollIdentifier, pollName, pollType, pollOptions, userCanChangeVote, chartType, optionsLabelDict, optionsLabelDictForGraph):
        from pkg_resources import resource_filename
        
        currentURL = self.getCurrentURL(req);
        id_param = self.getUrlParam(req, "pollid")
        current_logged_user = "-1"
        if req.authname is not None:
            current_logged_user = req.authname
        
#        identifier = None
#        pageType = None
#        if self.isWikiPage(currentURL)["success"]:
#            identifier = self.isWikiPage(currentURL)["identifier"]
#            pageType = "wiki"
#        elif self.isTicketPage(currentURL)["success"]:
#            identifier = self.isTicketPage(currentURL)["identifier"]
#            pageType = "ticket"
        
        
        pollId = pollIdentifier
        hash = self.getStringHash(pollId)
        data = {"pollIdentifier" : pollIdentifier, "pollTitle" : pollName, "pollType" : pollType, "pollOptions" : pollOptions, "hash" : hash, "currentUrl" : currentURL}
        
        dbObject = DB(self.env)
        pollData = dbObject.getPollById(hash)
        similarPollExist = self.checkIfPollAlreadyExist(pollData, data)
        
        votingSuccessful = "false"
        userHasPermissionToVote = True
        pollEditMessage = ""
        if similarPollExist:
            if id_param is not None and id_param == hash: #poll form has been posted
                tempPollOptions = pollData["poll_options"]
                tempPollVotes = pollData["poll_votes"]
                tempPollType = pollData["poll_type"]
                
                userHasPermissionToVote = True
                if current_logged_user == "anonymous" or current_logged_user is None or req.perm.has_permission('EASYPOLL_VOTE') != True:
                    userHasPermissionToVote = False
                    
                processUserVoting = True
                userAlreadyCastedVote = self.doesUserAlreadyCastVote(tempPollVotes, tempPollOptions, current_logged_user)['success'];
                if userCanChangeVote == "false" and userAlreadyCastedVote == True:
                    processUserVoting = False
                    
                if processUserVoting == True and userHasPermissionToVote == True:
                    if tempPollType == "single":
                        vote_param = self.getUrlParam(req, "rb")
                        if vote_param is not None:
                            if vote_param.strip() in tempPollOptions:
                                updateVoteDict = self.removeAlreadyCastedVotesByUser(tempPollVotes, current_logged_user);
                                if id_param == hash:
                                    if updateVoteDict.get(vote_param.strip(), None) is not None:
                                        alreadyCastedVoteList = updateVoteDict[vote_param.strip()]
                                    else:
                                        alreadyCastedVoteList = []
                                    alreadyCastedVoteList.append(current_logged_user)
                                    updateVoteDict[vote_param.strip()] = alreadyCastedVoteList
                                    dbObject.updatePollVotes(id_param, updateVoteDict)
                                    pollData = dbObject.getPollById(id_param)
                                    votingSuccessful = "true"
                            else:
                                pass
                    
                    elif tempPollType == "multiple":
                        optionSelected = []
                        for i in range(0, len(tempPollOptions)):
                            op = self.getUrlParam(req, "cb"+str(i))
                            if op is not None:
                                optionSelected.append(op)
    
                        updateVoteDict = self.removeAlreadyCastedVotesByUser(tempPollVotes, current_logged_user);
                        if id_param == hash:
                            for v in optionSelected:
                                if updateVoteDict.get(v.strip(), None) is not None:
                                    alreadyCastedVoteList = updateVoteDict[v.strip()]
                                else:
                                    alreadyCastedVoteList = []
                                alreadyCastedVoteList.append(current_logged_user)
                                updateVoteDict[v.strip()] = alreadyCastedVoteList
                            dbObject.updatePollVotes(id_param, updateVoteDict)
                            pollData = dbObject.getPollById(id_param)
                            votingSuccessful = "true"
        else:
            oldPollVotes = {}
            updatePollEntry = True
            oldPollId = None
            oldPollCreator = current_logged_user
            if pollData.get("poll_id", None) != None:
                oldPollId = pollData["poll_id"]
                oldPollVotes = pollData["poll_votes"]
                oldPollCreator = pollData["poll_creator"]
                if (oldPollCreator == current_logged_user and req.perm.has_permission('EASYPOLL_CREATE') == True) or (req.perm.has_permission('TRAC_ADMIN') == True) :
                    dbObject.deletePollById(hash)
                    updatePollEntry = True
                else:
                    updatePollEntry = False
                    pollEditMessage = "You don't have permission to update this poll"
                
            if updatePollEntry:
                if req.perm.has_permission('EASYPOLL_CREATE') or req.perm.has_permission('TRAC_ADMIN') == True:
                    dbObject.updatePollOptions(hash, pollIdentifier, pollName, pollType, pollOptions, oldPollVotes, oldPollCreator)
                    pollData = dbObject.getPollById(hash)
                    if oldPollId == None:
                        pollEditMessage = "Poll has been created successfully!"
                    else:
                        pollEditMessage = "Poll has been updated successfully!"
                else:
                    pollEditMessage = "You don't have permission to update this poll"
                    return self.getMsgTemplate("You don't have permission to create poll")
                    
            
        add_stylesheet(req, 'ep/css/style.css')
        add_script(req, 'ep/js/jquery.min.js')
        add_script(req, 'ep/js/highcharts.js')
        add_script(req, 'ep/js/modules/exporting.js')
        loader = TemplateLoader(
            resource_filename(__name__, 'templates'),
            auto_reload=True
        )
        
        userCanVote = "true"
        showResultChart = "false"
        tPollVotes = pollData.get("poll_votes", None)
        tPollOptions = pollData.get("poll_options", None)
        voteCastData = self.doesUserAlreadyCastVote(tPollVotes, tPollOptions, current_logged_user)
        userAlreadyCastedVote = voteCastData['success']
        userVotedData = voteCastData['votes']
        if userCanChangeVote == "false" and userAlreadyCastedVote == True:
            userCanVote = "false"
        
        if userAlreadyCastedVote:
            showResultChart = "true"    
        
        showUserNotHavePermissionToVoteMessage = "true"
        if userHasPermissionToVote:
            showUserNotHavePermissionToVoteMessage = "false"
            
        templateData = pollData
        templateData["currentUrl"] = currentURL
        templateData["user_can_vote"] = userCanVote
        templateData["show_result_chart"] = showResultChart
        templateData["user_votes"] = userVotedData
        tPollVotes = {}
        if pollData.get('poll_votes', None) is not None:
            tPollVotes = pollData['poll_votes']
            
        templateData["json_encoded_poll_votes"] = json.dumps(tPollVotes)
        templateData["chart_type"] = chartType
        templateData["show_thank_you_message"] = votingSuccessful
        templateData["show_user_has_no_permission"] = showUserNotHavePermissionToVoteMessage
        templateData["options_label_dict"] = optionsLabelDict
        templateData["poll_edit_message"] = pollEditMessage
        templateData["json_encoded_options_label_dict_graph"] = json.dumps(optionsLabelDictForGraph)
        
        tmplate = loader.load('easypoll.html')
        return tmplate.generate(data=templateData).render('html', doctype='html')
        
    def checkIfPollAlreadyExist(self, dbPollData, pollData):
        dbPollTitle = dbPollData.get("poll_title", None)
        pollTitle = pollData.get("pollTitle", None)
        if dbPollTitle is not None and pollTitle is not None:
            dbPollTitle = dbPollTitle.strip()
            pollTitle = pollTitle.strip()
            if pollTitle != dbPollTitle:
                return False
        else:
            return False
        
        dbPollIdentifier = dbPollData.get("poll_identifier", None)
        pollIdentifier = pollData['pollIdentifier']
        if dbPollIdentifier is not None and pollIdentifier is not None:
            dbPollIdentifier = dbPollIdentifier.strip()
            pollIdentifier = pollIdentifier.strip()
            if dbPollIdentifier != pollIdentifier:
                return False
        else:
            return False
        
        dbPollType =  dbPollData.get("poll_type", None)
        pollType = pollData.get("pollType", None)
        if dbPollType is not None and pollType is not None:
            dbPollType = dbPollType.strip()
            pollType = pollType.strip()
            if dbPollType != pollType:
                return False
        else:
            return False
        
        dbPollOptions =  dbPollData.get("poll_options", None)
        pollOptions = pollData.get("pollOptions", None)
        if dbPollOptions is not None and pollOptions is not None:
            if dbPollOptions != pollOptions:
                return False
        else:
            return False
        
        return True

    def removeAlreadyCastedVotesByUser(self, pollVotesDict, user):
        updateVoteDict = {}
        for key in pollVotesDict.keys():
            tempVotesSubmitted = pollVotesDict[key]
            if user in tempVotesSubmitted:
                tempVotesSubmitted.remove(user)
            updateVoteDict[key] = tempVotesSubmitted
        
        return updateVoteDict
    
    def doesUserAlreadyCastVote(self, pollVotesDict, pollOptions, user):
        returnData = {'votes' : [], 'success' : False}
        if pollVotesDict is not None and pollOptions is not None:
            for key in pollVotesDict.keys():
                if key in pollOptions:
                    tempVotesSubmitted = pollVotesDict[key]
                    if user in tempVotesSubmitted:
                        returnData["votes"].append(key)
                        returnData["success"] = True
                    
        return returnData
    
        
    def getCurrentURL(self, req):
        return self.env.href(req.path_info)
    
    def getUrlParam(self, req, param):
        returnValue = None
        if param is not None:
            qDict = req.args
            if qDict.get(param) is not None:
                returnValue = qDict[param]
        
        return returnValue
        
    def getUrlParams(self, url, param = None):
        urlQueryString = urlparse.urlsplit(url).query
        returnValueDict = {}
        returnValue = None
        if urlQueryString is not None and urlQueryString is not "":
            splitD = urlQueryString.split("&")
            for q in splitD:
                tempSplitD = q.split("=")
                if len(tempSplitD) > 0:
                    if param is not None:
                        if tempSplitD[0] == param:
                            returnValue = tempSplitD[1]
                            break
                    else:
                        returnValueDict[tempSplitD[0]] = tempSplitD[1]
        
        if param is not None:
            return returnValue
        else:
            return returnValueDict
    
        
    def isWikiPage(self, url):
        url = url.strip()
        returnValue = {"success" : False}
        if url is not None and url is not "":
            splitData = url.split("/")
            if len(splitData) > 0:
                if splitData[len(splitData)-2] == "wiki":
                    returnValue = {"success" : True, "identifier" : splitData[len(splitData)-1]}
        
        return returnValue            

    def isTicketPage(self, url):
        url = url.strip()
        returnValue = {"success" : False}
        if url is not None and url is not "":
            splitData = url.split("/")
            if len(splitData) > 0:
                if splitData[len(splitData)-2] == "ticket":
                    tempTicketId = splitData[len(splitData)-1]
                    tempSD = tempTicketId.split("#")
                    returnValue = {"success" : True, "identifier" : tempSD[0]}
        return returnValue
    
    def getStringHash(self, string):
        return hashlib.sha224(string).hexdigest()
#        return str(hash(string))
        
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ep', resource_filename(__name__, 'htdocs')), ('ept', resource_filename(__name__, 'templates'))]
        
    def get_permission_actions(self):
        return ('EASYPOLL_CREATE', 'EASYPOLL_VOTE') 
    
    def getMsgTemplate(self, msg):
        str = ''
        str += '<div class="form-container">'
        str += '<div style="margin-left:10px;width:30%;">'
        str +=  '<div class="errors" style="text-align:center;">'
        str +=      msg
        str +=  '</div>'
        str += '</div>'
        str += '</div>'
        return str
        
class DB(object):
    
    def __init__(self, env):
        self.env = env
        self.tableName = "easypoll"
        
    def updatePollOptions(self, poll_id, poll_identifier, poll_title, poll_type, poll_options, poll_votes, poll_creator):
        poll_options_str = json.dumps(poll_options)
        poll_votes_str = json.dumps(poll_votes)
        
        poll_id = poll_id.strip()
        
        poll_title = str(poll_title.strip())
         
        poll_title = poll_title.encode('utf8')
        poll_title = poll_title.replace("'","’")
#        poll_title = poll_title.encode('string_escape')
#        poll_title = poll_title.encode('utf8')
#        print poll_title
#        print poll_title
#        print 'you f food\\xe4\\xb8\\xad\\xe6\\x96\\x87?'

        
        poll_identifier = str(poll_identifier.strip())
        poll_identifier = poll_identifier.encode('string_escape')
        
        poll_type = str(poll_type.strip())
        poll_type = poll_type.encode('string_escape')
        
        sql = "INSERT INTO " + self.tableName + " ( poll_id, poll_identifier, poll_type, poll_title, poll_options, poll_votes, poll_creator) VALUES ('%s' , '%s', '%s', '%s', '%s', '%s', '%s')" % (poll_id, poll_identifier, poll_type, poll_title, poll_options_str, poll_votes_str, poll_creator)
        print sql
        try:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute(sql)
            db.commit()
        except:
            self.env.log.debug("::::: sql error in updatePollOptions :::::: %s " % (sql))
    
    def deletePollById(self, poll_id):
        sql = "DELETE FROM " + self.tableName + " WHERE poll_id = '%s'" % (poll_id)
        try:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute(sql)
            db.commit()
        except:
            self.env.log.debug("::::: sql error in deletePollById :::::: %s " % (sql))
            
    
    def updatePollVotes(self, poll_id, poll_votes):
        poll_votes_str = json.dumps(poll_votes)
        poll_id = poll_id.strip()
        sql = "UPDATE " + self.tableName + " SET poll_votes = '%s' WHERE poll_id = '%s'" % (poll_votes_str, poll_id)
        try:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute(sql)
            db.commit()
        except:
            self.env.log.debug("::::: sql error in updatePollVotes :::::: %s " % (sql))
        
        
    def getPollById(self, poll_id):
        sql = "SELECT * FROM " + self.tableName + " WHERE poll_id = '%s'" % (poll_id)
        returnResult = {}
        try:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute(sql)
            for row in cursor:
                returnResult["poll_id"] = row[1]
                returnResult["poll_identifier"] = row[2].decode('string_escape', 'ignore')
                returnResult["poll_type"] = row[3].decode('string_escape', 'ignore')
                returnResult["poll_title"] = row[4].decode('string_escape', 'ignore')
                returnResult["poll_options"] = eval(row[5])
                returnResult["poll_votes"] = eval(row[6])
                returnResult["poll_creator"] = row[7]
                break;
        except:
            self.env.log.debug("::::: sql error in getPollById :::::: %s " % (sql))
        return returnResult
        
