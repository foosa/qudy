"""
PLOT.PY

Routines to produce plots and figures.

Copyright (C) 2011, 2012 True Merrill and JP Addison
Georgia Institute of Technology
School of Chemistry and Biochemistry

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import quantop as qu
import routines as ro

__all__ = ['controls','scaling','profile','enabled']

# Plotting functionality is built on matplotlib, however this is not a
# dependency to run qudy.  Plotting functionality will be disabled if
# matplotlib is not present on the system.

try:
    import matplotlib.pyplot as plt
    enabled = True

except ImportError:
    enabled = False


def controls( ctrl ):
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
    # Attempt to plot the controls.  If matplotlib does not exist
    # on the system, alert the user.

    if not enabled:
        raise ImportError('\'controls\' requires matplotlib for' + \
                          ' plotting functionality.')
    
    # Create figure handles, and a subplot for axis scaling
    fig = plt.figure()
    ax = plt.subplot(111)

    # Plot control functions
    for index in range( ctrl.number_controls ):
        label = '$u_{%i}$' %(index)
        ax.plot( ctrl.times, ctrl.control[:,index], label=label )

    # Ensure that the axes are resonably scaled
    c_max = ctrl.control.max()
    c_min = ctrl.control.min()
    scale = c_max - c_min
    ds = 0.1 * scale
    plt.axis([ ctrl.timemin(), ctrl.timemax(), c_min-ds, c_max+ds])

    # Labels and annotations
    plt.xlim( (ctrl.timemin(), ctrl.timemax()) )
    plt.xlabel(r'$t$')
    plt.ylabel(r'$u_\mu(t)$')
    plt.title('Control functions')

    # Shrink size of axis by 7%.  Add a legend.
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width*0.93, box.height])
    ax.legend(bbox_to_anchor=(1., 0.5), loc='center left')
    plt.show()



def scaling( sequence, target, **keyword_args ):
    """
    Makes a log-log scaling plot of a sequence infidelity relative to a target gate.
    """
    
    # Parse keyword arguments.
    if keyword_args.has_key('min_epsilon'):
        min_epsilon = keyword_args['min_epsilon']
    else:
        min_epsilon = 1e-5

    if keyword_args.has_key('max_epsilon'):
        max_epsilon = keyword_args['max_epsilon']
    else:
        max_epsilon = 1

    if keyword_args.has_key('points'):
        points = keyword_args['points']
    else:
        points = 500.0

    if keyword_args.has_key('show'):
        show = keyword_args['show']
    else:
        show = True
        
    
    # Create a set of error amplitudes to measure scaling
    log_epsilon = qu.arange( qu.log10(min_epsilon), qu.log10(max_epsilon), \
                  (qu.log10(max_epsilon) -qu.log10(min_epsilon))/float(points) )

    epsilon = []
    err = sequence.error.copy()
    for index in range( len(log_epsilon) ):
        epsilon.append( 10**log_epsilon[index] )

    # Compute matrix representation of target gate
    try:
        Ut = target.solve()
    except AttributeError:
        Ut = target

    # Measure infidelities
    infidelities = []
    for index in range( len(epsilon) ):
        
        e = epsilon[index]
        err.error_parameters = [ e ]
        sequence.update_error(err)
        infidelities.append( \
            ro.infidelity(sequence.solve() , target.solve()) )
    
    if show:
        
        # Create plot
        plt.loglog( qu.real(epsilon) , qu.real( infidelities ) )
        plt.xlabel(r'Systematic Error')
        plt.ylabel(r'Infidelity')
        plt.show()
        
    else:
        
        # Return data to user
        return [ qu.real(epsilon) , qu.real(infidelities) ]



def profile( sequence, target, **keyword_args ):
    """
    Makes a log-log scaling plot of a sequence infidelity relative to a target gate.
    """
    
    # Parse keyword arguments.
    if keyword_args.has_key('min_epsilon'):
        min_epsilon = keyword_args['min_epsilon']
    else:
        min_epsilon = -1

    if keyword_args.has_key('max_epsilon'):
        max_epsilon = keyword_args['max_epsilon']
    else:
        max_epsilon = 1

    if keyword_args.has_key('points'):
        points = keyword_args['points']
    else:
        points = 500.0

    if keyword_args.has_key('show'):
        show = keyword_args['show']
    else:
        show = True

    if keyword_args.has_key('label'):
        label = keyword_args['label']
    else:
        label = None

    if keyword_args.has_key('calculation'):
        calculation = keyword_args['calculation']
    else:
        calculation = 'infidelity'
        
    
    # Create a set of error amplitudes to measure scaling
    dE  = max_epsilon - min_epsilon
    epsilon = qu.arange( min_epsilon, max_epsilon + dE/points, dE / points )

    # Compute matrix representation of target gate
    if hasattr( target, 'solve' ):
        Ut = target.solve()
    else:
        Ut = target

    # Perform calculation
    err = sequence.error.copy()
    y = []
    for index in range( len(epsilon) ):
        
        e = epsilon[index]
        err.error_parameters = [ e ]
        sequence.update_error(err)

        if calculation == 'infidelity':
            y.append( ro.infidelity(sequence.solve() , Ut) )

        elif calculation == 'population':
            p0 = qu.operator("0,0;0,1")
            p1 = qu.operator("1,0;0,0")
            U = sequence.solve()
            y.append( qu.trace( U*p0*U.H*p1 ) )
    
    if show:
        
        # Create plot
        if label == None:
            plt.plot( qu.real(epsilon) , qu.real( y ) )
        else:
            plt.plot( qu.real(epsilon) , qu.real( y ), label = label )
            
        plt.xlabel(r'Systematic Error')

        if calculation == 'infidelity':
            plt.ylabel(r'Infidelity')
            
        elif calculation == 'population':
            plt.ylabel(r'Population')
            
        plt.xlim([min_epsilon, max_epsilon]) 
        plt.show()
        
    else:
        
        # Return data to user
        return [ qu.real(epsilon) , qu.real(y) ]
