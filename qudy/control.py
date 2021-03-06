# CONTROL.PY
#
# A class for quantum control functions
# 
# Copyright (C) 2011, 2012 True Merrill
# Georgia Institute of Technology
# School of Chemistry and Biochemistry
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from quantop import *
from numpy import all, diff, interp
import plot as qudyplot

__all__ = ['control','load','save']

class control:
    """
    class for quantum control functions.  
    
    Inputs may be single-variable functions which accept and return a
    single real number (i.e., an int, double, or float) or an input
    may be a time-ordered list of control values (i.e., an instance of
    the list, array, or matrix class).
    
    **Forms:**
    
       *Pure Arrays*
          
          1.  ``control( arr, t_arr )``
          2.  ``control( arr_1, arr_2, t_arr )``
          3.  ``control( arr_1, arr_2, ... , arr_k, t_arr )``
          4.  ``control( ARR )``
          
       *One-Parameter Functions*
          
          1.  ``control( u, t_arr )``
          2.  ``control( u_1, u_2, t_arr )``
          3.  ``control( u_1, u_2, ... , u_k, t_arr )``
          
       *Mixed Forms*
          
          1.  ``control( arr_1, u_2, ... , t_arr )``
          2.  ``control( u_1, arr_2, ... , t_arr )``
          
    **Args:**
          
       * *arr* : An n-element object of real-valued parameters.  
       * *t_arr* : An n-element object of real-valued time vales.  
         The elements should be time-ordered.
       * *ARR* : An (n,k+1) dimensional array containing both 
         amplitude data and time data.  Each column corresponds to 
         an independent component of the control function, excepting 
         the final column which corresponds to the time data *t_arr*.
         k is the dimensionality of the control function.
       * *u* : A function which inputs a real-valued time parameter 
         and returns a control amplitude.
       
    **Optional keys:**
       
       interpolation = 'method' : Chooses an interpolation method. 
       the method may be one of the following options.
       
          1.  'latest' :  most recent control value in time
          2.  'nearest' : nearest control value in time
          3.  'linear' : use linear interpolation between values
       
       verbose = 'bool' : Boolean flag sets verbosity of outputs.
          
    **Raises:**
       
       * ``TypeError`` : Inputs are of incorrect type.
       * ``ValueError`` : Inputs are improperly valued.
       
    Control objects have several important properties, for instance they may be
    called as functions.  Interpolation is used to estimate the value of the 
    controls at any instant of time within the time interval.
    """
    
    def __init__( self, *args, **keyword_args ):
        """Initialize the control instance."""
        
        # If there is more than one argument, then the last must be an
        # array of time values, e.g. t_arr.
        if len( args ) > 1:
            
            # Check that t_arr is an array
            t_arr = args[ len(args) - 1 ]
            try:
                t_arr = t_arr.__array__()
                self.times = t_arr.flatten()
                self.times.shape = (len(self.times),1)
                # self.timemax = t_arr.max()
                # self.timemin = t_arr.min()
                
            except AttributeError:
                raise TypeError('Time values must be an array type.')

            ARR = copy( self.times )
            for index in range( len(args) - 1 ):
                
                # Loop over arguments from last to first.  Easist to
                # keep time vector in the correct position on ARR.
                arg = args[-(index + 2)]
                
                # Is arg a function? Map to a discrete array.
                if hasattr( arg, '__call__' ):
                    arr = array( map( arg , self.times ) )
                    arr.shape = (len(self.times),1)
                    ARR = hstack(( arr , ARR ))
                    
                # Is arg an array? Check that it is of proper length.
                elif hasattr( arg , '__array__' ):
                    arr = arg
                    
                    # Orient arrays in the correct direction
                    if len( arr.shape ) == 1:
                        arr.shape = ( len(arr) , 1 )
                    
                    if arr.shape[0] == len(self.times):
                        ARR = hstack(( arr , ARR ))
                        
                    else:
                        raise ValueError('Dimension mismatch.')
                    
                # Then arg was not understood, throw an error.
                else:
                    raise TypeError('The following argument was not ' + \
                          'understood: \n\n%s\n' %( str(arg) ))
                 
            # Count number of controls
            number_controls = ARR.shape[1] - 1
            
            # Save relevant data to self
            self.control = ARR[:, 0:number_controls]
            self.number_controls = number_controls
            self.dimension = number_controls
                    
        # Otherwise the input must be one large array, e.g. input ARR.
        # The last column is interpreted as the time vector, and the
        # remaining columns as control functions.
        else:
            
            arg = args[0]
            try:
                ARR = arg.__array__()
                number_controls = ARR.shape[1] - 1
                
                # Grab time vector (last column).
                self.times = ARR[: , number_controls]
                # self.timemax = max( self.times )
                # self.timemin = min( self.times )
                
                # Assign remaining controls.
                self.control = ARR[: , 0:(number_controls)]
                self.number_controls = number_controls
                self.dimension = number_controls
            
            except AttributeError:
                raise TypeError('Input is of an improper type.')
            
        # Fix shape of time array
        self.times.shape = ( len(self.times) , 1 )
                
        # Sanity checks: see that times is increasing
        if not all( diff( self.times ) > 0 ):
            raise ValueError('Time array is not time-ordered.')
 
        
        # Parse keyword arguments.  Sets default interpolation.  Other
        # keywords that are not understood will be quietly ignored.
        if keyword_args.has_key( 'interpolation' ):
            
            interpolation = keyword_args['interpolation']
            valid_inputs = [ 'latest' , 'nearest' , 'linear' ]
            
            if interpolation in valid_inputs:
                self.interpolation = interpolation
                
            else:
                # Keyword was not valid.  Warn user and default to
                # 'latest' type interpolation.
                self.interpolation = 'latest'
                warn('Interpolation type not understood, defaulting to \'latest\'')
        
        else:
            # Set default interpolation.
            self.interpolation = 'latest'
            
        # Check verbosity flag
        if keyword_args.has_key( 'verbose' ):
            
            flag = keyword_args['verbose']
            if type(flag) == type(True):
                self.verbose = flag
            
            else:
                raise TypeError('\'verbose\' flag must be Boolean.')
                
        else:
            # Set default verbosity
            self.verbose = False
            
            
    def __repr__( self ):
        """Function to display control objects when called on the
        command line."""
        string = str( self.dimension ) + '-D control on t = ( ' + \
                 str( self.timemin() ) + ' , ' + str( self.timemax() ) + ' )'
        
        if self.verbose:
            string = string + '\n' + str( self.control ) + '\n'
        
        return string
    
    
    def __call__(self, *args ):
        """
        Returns the value of the control functions as a specific
        instance of time.  Interpolation is used.
        """
        
        if len(args) == 1:
            # Only a time was specified, return control vector.
            t = args[ 0 ]
            return self.interpolate( t )
        
        elif len(args) == 2:
            # Both a component and time were specified, return component.
            index = args[ 0 ]
            t = args[ 1 ]
            return self.interpolate( t )[ index ]
        
        
    def __len__(self):
        """
        length of the control.  Returns self.number_controls
        """
        return self.number_controls
    
    
    def timemin(self):
        """
        Returns the minimum time slice.
        """
        return float( min(self.times) )
    
    
    def timemax(self):
        """
        Returns the maximum time slice.
        """
        return float( max(self.times) )
    
    
    def copy(self):
        """
        Creates an independent copy of self in memory.
        """
        
        ctrl = self.control.copy()
        times = self.times.copy()
        c = control( ctrl, times )
        c.interpolation = str( copy( self.interpolation ) )
        c.verbose =  bool( copy( self.verbose ) )
        
        return c


    def arc_length(self):
        """
        Measures arc length of self on the Lie algebra.  Assume
        orthogonal coordinates.

        .. todo:
        
           Consider a generalization which allows for a non-orthogonal
           assumption.
        """

        length = 0
        for timestep in range( len(self.times) - 1 ):

            # Calculate pulse duration
            dt = self.times[ timestep + 1 ] - self.times[ timestep ]
            dt = float(dt)

            # Calculate interval Lie "length"
            dL = norm( self.control[ timestep, : ] ) * dt
            length = length + dL

        return length
    
    
    def inverse(self):
        """
        function to invert controls.
        
        An inverted set of controls defines a control system which
        produces an inverse, i.e., backwards propagation.  The time
        ordering of each control slice is reversed (time flows
        backwards) and each of the components of the control functions
        are negated.
        """
        
        # Make a copy of self to work with.  Flip the time ordering
        # and invert the control components.
        c = self.copy()
        c.control = - flipud( c.control )
        c.times = c.timemax() - flipud( c.times )
        
        return c
        
                
    def interpolate( self, time, interpolation = None ):
        """
        function to interpolate controls.
        
        At the core, a control instance is an array of values
        corresponding set of control functions sampled over discrete
        time intervals.  Interpolation may be used to estimate the
        values of the control functions at times other than those
        explicitly sampled.  Several interpolation methods exist.
        
        Consider the following code.
        
        .. code-block:: python
           
           u1 = lambda x: sin(x)
           u2 = lambda x: cos(x)
           t = arange( 0, 2*pi, pi/10.0 )
           c = control( u1, u2, t )
        
        The control functions u1 and u2 have been sampled at a
        discrete set of times, t.  To extimate the controls for a time
        not in t, we may use interpolation.
           
        **Args:**
           
           * *time* : A real-valued time value.
        
        **Optional Keys:**
           
           * interpolation = 'method' : Chooses an interpolation 
             method.  The method may be one of the following.
           
              1. 'latest' : returns most recent control value in time.
              2. 'nearest' : returns nearest control value in time.
              3. 'linear' : uses linerar interpolation between nearest
                 two control values.
              
        **Raises:**
           
           * ``ValueError`` : time is not within sampling interval.
           * ``ValueError`` : interpolation method not recognized.

        **Returns:** 
           
           * interp_controls : interpolated control vector. 
        """
        # If no input has been specified, then set default
        # interpolation.
        
        if interpolation == None:
            interpolation = self.interpolation
        
        # Check that time lies within the control interval.
        if (time < self.timemin()) or (time > self.timemax()):
            raise ValueError('Interpolation time must lie within the' + \
                  ' interval ( %.2E , %.2E ).' %(self.timemin(),self.timemax()) )
        
        # Calculate closest points that will form the interpolation
        # interval t_low < time < t_high.
        
        try:
            t_low = max( self.times[ self.times - time < 0 ] )
        except ValueError:
            # We must be at the lower time limit 
            t_low = self.timemin()
            
        try:
            t_high = min( self.times[ self.times - time > 0 ] )
        except ValueError:
            # We must be at the higher time limit
            t_high = self.timemax()
        
        index_low = self.times.tolist().index( t_low )
        index_high = self.times.tolist().index( t_high )
        
        
        if interpolation == 'latest':
            # Return most recent control value.
            return self.control[index_low,:]
        
        elif interpolation == 'nearest':
            # Return control value closest to time in question.
            if (time - t_low) <= (t_high - time):
                return self.control[index_low,:]
            else:
                return self.control[index_high,:]
        
        elif interpolation == 'linear':
            # Linear interpolation between control values.
            interp_controls = []
            for index in range( self.number_controls ):
                tp = [t_low, t_high ]
                yp = [self.control[index_low, index], self.control[index_high, index]]
                val = interp( time, tp, yp )
                interp_controls.append(val)
                
            return array( interp_controls )
                
        else:
            raise ValueError('Interpolation method not recognized.')
        
        
    def plot( self ):
        """
        Plots the control functions.  The plotting functionality
        requires the python matplotlib module.
        
        **Example:**
        
           .. code-block:: python
              
              ux = lambda t: cos( pi * t )
              uy = lambda t: sin( pi * t )
              uz = lambda t: 0
              dt = 1.0 / 150.0
              t = arange( 0, 1 + dt, dt )
              
              # Create the control instance
              ctrl = control( ux, uy, uz, t )

              # Make a plot
              ctrl.plot()
              
           .. _(1):

           .. figure:: _images/control_example.*
	 
              Plot generated by ``control.plot()``.

           .. .. only:: latex

           ..    .. figure:: _images/control_example.pdf
           
           .. .. only:: html
           
           ..    .. figure:: _images/control_example.svg
        
        **Raises:**
           
           * ``ImportError`` : requires matplotlib for plotting functionality.
        """
        ## # Attempt to plot the controls.  If matplotlib does not exist
        ## # on the system, alert the user.
        ## try:
        ##     import matplotlib.pyplot as plt
        ## except ImportError:
        ##     raise ImportError('\'control.py\' requires matplotlib for' + \
        ##                       ' plotting functionality.')
        
        ## # Create figure handles, and a subplot for axis scaling
        ## fig = plt.figure()
        ## ax = plt.subplot(111)
        
        ## # Plot control functions
        ## for index in range( self.number_controls ):
        ##     label = '$u_{%i}$' %(index)
        ##     ax.plot( self.times, self.control[:,index], label=label )
        
        ## # Ensure that the axes are resonably scaled
        ## c_max = self.control.max()
        ## c_min = self.control.min()
        ## scale = c_max - c_min
        ## ds = 0.1 * scale
        ## plt.axis([ self.timemin(), self.timemax(), c_min-ds, c_max+ds])
            
        ## # Labels and annotations
        ## plt.xlim( (self.timemin(), self.timemax()) )
        ## plt.xlabel(r'$t$')
        ## plt.ylabel(r'$u_\mu(t)$')
        ## plt.title('Control functions')
        
        ## # Shrink size of axis by 7%.  Add a legend.
        ## box = ax.get_position()
        ## ax.set_position([box.x0, box.y0, box.width*0.93, box.height])
        ## ax.legend(bbox_to_anchor=(1., 0.5), loc='center left')
        ## plt.show()
        
        ## # Cleanup
        ## del plt
        return qudyplot.controls( self )
        
    
    def save( self, filename, format = 'csv' ):
        
        # Concat the controls and the time vector to form an array
        import numpy
        ARR = numpy.hstack( ( self.control , self.times ) )
        
        if format == 'csv':
            # Construct headers, footers, etc
            try:
                import datetime
                now = datetime.datetime.now()
                timestamp = "%i-%i-%i" %(now.year, now.month, now.day)
            
            except ImportError:
                timestamp = "X-X-X"
            
            HEADER = "# QUDY\n" +\
                     "# CONTROL SPECIFICATION FORMAT\n" +\
                     "#\n" +\
                     "# FILENAME : '%s'\n" %(filename + ".csv") +\
                     "# DATE : %s\n" %(timestamp) +\
                     "#\n" +\
                     "# This file specifies a set of control functions for a quantum control\n" +\
                     "# system.  Each column (excluding the final column) corresponds to a\n" +\
                     "# single control function sampled over a discrete set of time values.\n" +\
                     "# The final column represents the discrete time values that the\n" +\
                     "# control functions are sampled over.\n" +\
                     "#\n"
            
            FOOTER = 'This is the footer string.'
            FORMAT = '%.12e'
            DELIMITER = ',\t'
            
            # Header and footer support will be added in numpy version
            # 2.0 or greater.  Currently, we cannot assume that the
            # user is using these newer packages.
            
            f = open( filename + '.csv' , 'w' )
            numpy.savetxt(f, ARR, FORMAT, DELIMITER) 
            f.close()
            
            # Manually add the header
            f = open( filename + '.csv' , 'r+')
            data = f.read()            # read everything in the file
            f.seek(0)                  # rewind
            f.write(HEADER + data)     # write the new line before
            f.close()
            
            if self.verbose:
                print 'Saved to %s' %(filename + '.csv') 
            
        
        elif format == 'npy':
            f = open( filename + '.npy' , 'w' )
            numpy.save( f , ARR )
            f.close()
            if self.verbose:
                print 'Saved to %s' %(filename + '.npy')
            
        elif format == 'npz':
            f = open( filename + '.npz' , 'w' )
            numpy.savez( f, ARR )
            f.close()
            if self.verbose:
                print 'Saved to %s' %(filename + '.npy')
        
        else:
            # format not recognized
            raise ValueError('Format not recognized.')
                
        # Cleanup
        del numpy


def load( filename, format = None ):
    """A function to load saved control instances"""
    
    # Check that filename is either a file or a string
    if type(filename) == file:
        f = filename
    elif type(filename) == str:
        f = open( filename, 'r' )
    else:
        raise ValueError('Input must be either a string or file object.')
    
    # By default, guess the format based on the extension
    if format == None:
        import os.path
        format = os.path.splitext(filename)[1][1:]
    
    # Reconstitute array preconstructor    
    import numpy
    if format == 'csv':
        ARR = numpy.loadtxt(f, delimiter = ',\t')
    
    elif format == 'npy':
        ARR = numpy.load(f)
        
    elif format == 'npz':
        dictionary = numpy.load(f)
        ARR = dictionary['arr_0']
        
    else:
        raise ValueError('The format %s was not recognized' %(format))
    
    del numpy
    
    # Return a control object
    return control(ARR)


def save( ctrl, filename, format = 'csv' ):
    """
    A function to save control instances
    """
    ctrl.save(filename, format)
