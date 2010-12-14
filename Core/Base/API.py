########################################################################
# $HeadURL: svn+ssh://svn.cern.ch/reps/dirac/DIRAC/trunk/DIRAC/Core/Base/API.py $
# File :   API.py
########################################################################
__RCSID__ = "$Id: API.py 19233 2009-12-04 22:40:35Z acsmith $"

""" DIRAC API Base Class """

from DIRAC.Core.Base                import Script
Script.initialize()

from DIRAC                          import gConfig, gLogger, S_OK, S_ERROR
from DIRAC.Core.Utilities.List      import sortList
from DIRAC.Core.Security.Misc       import getProxyInfo, formatProxyInfoAsString
from DIRAC.Core.Security.CS         import getDNForUsername

import string, pprint, sys

COMPONENT_NAME = 'API'

class API:

  #############################################################################
  def __init__( self ):
    self.log = gLogger.getSubLogger( COMPONENT_NAME )
    self.section = COMPONENT_NAME
    self.pPrint = pprint.PrettyPrinter()
    #Global error dictionary
    self.errorDict = {}

  #############################################################################
  def _errorReport( self, error, message = None ):
    """Internal function to return errors and exit with an S_ERROR() """
    if not message:
      message = error
    self.log.warn( error )
    return S_ERROR( message )

  #############################################################################
  def _printFormattedDictList( self, dictList, fields, uniqueField, orderBy ):
    """ Will print ordered the supplied field of a list of dictionaries """
    orderDict = {}
    fieldWidths = {}
    dictFields = {}
    for dict in dictList:
      for field in fields:
        fieldValue = dict[field]
        if not fieldWidths.has_key( field ):
          fieldWidths[field] = len( str( field ) )
        if len( str( fieldValue ) ) > fieldWidths[field]:
          fieldWidths[field] = len( str( fieldValue ) )
      orderValue = dict[orderBy]
      if not orderDict.has_key( orderValue ):
        orderDict[orderValue] = []
      orderDict[orderValue].append( dict[uniqueField] )
      dictFields[dict[uniqueField]] = dict
    headString = "%s" % fields[0].ljust( fieldWidths[fields[0]] + 5 )
    for field in fields[1:]:
      headString = "%s %s" % ( headString, field.ljust( fieldWidths[field] + 5 ) )
    print headString
    for orderValue in sortList( orderDict.keys() ):
      uniqueFields = orderDict[orderValue]
      for uniqueField in sortList( uniqueFields ):
        dict = dictFields[uniqueField]
        outStr = "%s" % str( dict[fields[0]] ).ljust( fieldWidths[fields[0]] + 5 )
        for field in fields[1:]:
          outStr = "%s %s" % ( outStr, str( dict[field] ).ljust( fieldWidths[field] + 5 ) )
        print outStr

  #############################################################################
  def _prettyPrint( self, object ):
    """Helper function to pretty print an object. """
    print self.pPrint.pformat( object )

  #############################################################################
  def _promptUser( self, message, choices = ['y', 'n'], default = 'n' ):
    """Internal function to pretty print an object. """
    if ( choices ) and ( default ) and ( not default in choices ):
      return S_ERROR( "The default value is not a valid choice" )
    choiceString = ''
    if choices and default:
      choiceString = string.join( choices, '/' ).replace( default, '[%s]' % default )
    elif choices and ( not default ):
      choiceString = string.join( choices, '/' )
    elif ( not choices ) and ( default ):
      choiceString = '[%s]' % default

    if choiceString:
      self.log.info( '%s %s :' % ( message, choiceString ) )
    elif default:
      self.log.info( '%s %s :' % ( message, default ) )
    else:
      self.log.info( '%s :' % message )
    response = raw_input()
    promptAgain = False
    if ( not response ) and ( default ):
      response = default
    elif ( not response ) and ( not default ):
      promptAgain = True
    elif ( response ) and ( choices ) and ( not response in choices ):
      promptAgain = True

    if promptAgain:
      if choices:
        self.log.info( 'Possible responses are: %s' % ( string.join( choices, ', ' ) ) )
      if choiceString:
        self.log.info( '%s %s :' % ( message, choiceString ) )
      elif default:
        self.log.info( '%s %s :' % ( message, default ) )
      else:
        self.log.info( '%s :' % message )
      response = raw_input()
      if ( response ) and ( choices ) and ( not response in choices ):
        gLogger.error( "Failed to determine user selection" )
        return S_ERROR( "Failed to determine user selection" )
      elif ( not response ) and ( not default ):
        gLogger.error( "Failed to determine user selection" )
        return S_ERROR( "Failed to determine user selection" )
    return S_OK( response )

  #############################################################################
  def _getCurrentUser( self ):
    res = getProxyInfo( False, False )
    if not res['OK']:
      return self._errorReport( 'No proxy found in local environment', res['Message'] )
    proxyInfo = res['Value']
    gLogger.debug( formatProxyInfoAsString( proxyInfo ) )
    if not proxyInfo.has_key( 'group' ):
      return self._errorReport( 'Proxy information does not contain the group', res['Message'] )
    res = getDNForUsername( proxyInfo['username'] )
    if not res['OK']:
      return self._errorReport( 'Failed to get proxies for user', res['Message'] )
    return S_OK( proxyInfo['username'] )

  #############################################################################
  def _reportError( self, message, name = '', **kwargs ):
    """Internal Function. Gets caller method name and arguments, formats the 
       information and adds an error to the global error dictionary to be 
       returned to the user. 
    """
    className = name
    if not name:
      className = __name__
    methodName = sys._getframe( 1 ).f_code.co_name
    arguments = []
    for key in kwargs:
      if kwargs[key]:
        arguments.append( '%s = %s ( %s )' % ( key, kwargs[key], type( kwargs[key] ) ) )
    finalReport = 'Problem with %s.%s() call:\nArguments: %s\nMessage: %s\n' % ( className, methodName, string.join( arguments, ', ' ), message )
    if self.errorDict.has_key( methodName ):
      tmp = self.errorDict[methodName]
      tmp.append( finalReport )
      self.errorDict[methodName] = tmp
    else:
      self.errorDict[methodName] = [finalReport]
    self.log.verbose( finalReport )
    return S_ERROR( finalReport )

  #############################################################################
  def _getErrors( self ):
    """Returns the dictionary of stored errors.
    """
    return self.errorDict
