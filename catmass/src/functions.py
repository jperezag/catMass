# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 15:06:18 2021

@author: ashoff
"""

############################
#   Packages and Modules   #
############################

import numpy as np
import xraylib


##################
#    FUNCTIONS   #
##################


def XASMassCalc(Sample, Element, Edge, Area, AL = 2.5, delta = 50):
    '''
    Calculates the Edge energy [eV], sample mass [mg] and transmission edge step
    based upon a stoichiometric sample composition, the element and corresponding
    edge to be probed, the perpendicular cross-sectional area of the sample to
    the beam, desired total absorption lenght "delta" eV above the edge.
    
    delta is used to calcualte the absorption coefficient at E0+/-delta to determine
    the edge step

    Parameters
    ----------
    Sample : STR
        Chemcial formula of the sample. parentheses can be used. Numbers of 
        atoms are placed to the left of the atomic symbol (case sensitive)
        with no special characters. E.g. 'H2' or H2O, Na2SO4, or Pt0.5MgO.
    Element : STR
        Element in the sample at whihc to caluclate the absorption properties around.
    Edge : STR
        ['K', 'L1', 'L2', 'L3'] used to determine the edge energy of Element.
    Area : FLOAT
        [units = cm^2] cross-sectional area of sample in the X-ray beam. When
        determining sample mass, assume cross-sectional area of entire sample
        area in sample holder is being illuminated.
    AL : FLOAT, optional
        Desired total absorption cross-section of the sample at delta eV above
        the edge. Tthe default is 2.5.
    delta : FLOAT, optional
        Energy aove the edge energy to calcualte the sampel mass at and energy
        around the edge energy [E0+/- delta] to calcualte the tranmission edge
        step. The default is 50.

    Returns
    -------
    E0 : FLOAT
        Energy [eV] of the absopriton edge of the Element
    mass : FLOAT
        Mass [mg] calcuated based upon sample composition, energy, area, and total absorption
    step : FLOAT
        Estimated edge step of the element assuming transmission geometry

    '''

    #Placeholder Values to be updated by function
    delta = delta/1000 # converts eV to keV for xraylib calculation
    E0 = 0
    mass = 0
    step = 0
        
    #Extract Chemcial Information from Sample
    Elements = xraylib.CompoundParser(Sample)
    
    #Extract Chemcial Information from Absorbing Element
    edge_Element = xraylib.AtomicNumberToSymbol(xraylib.CompoundParser(Element)['Elements'][0])
        
    #Identify Edge Energy
    if Edge == 'K':
        E0 = xraylib.EdgeEnergy(xraylib.SymbolToAtomicNumber(edge_Element),0)
    elif Edge == 'L1':
        E0 = xraylib.EdgeEnergy(xraylib.SymbolToAtomicNumber(edge_Element),1)
    elif Edge == 'L2':
        E0 = xraylib.EdgeEnergy(xraylib.SymbolToAtomicNumber(edge_Element),2)        
    elif Edge == 'L3':
        E0 = xraylib.EdgeEnergy(xraylib.SymbolToAtomicNumber(edge_Element),3)
        

    if Elements['nElements']>1:
        # Determine Photabsorption Cross Sections for each element at E0 +/- 50 eV
        Photo_XS = []
        for x in range(0,Elements['nElements']):
            if x == 0:
                Photo_XS = [xraylib.CS_Photo(Elements['Elements'][x], E0-0.05), xraylib.CS_Photo(Elements['Elements'][x], E0+0.05)]
            else:
                newPXS = [xraylib.CS_Photo(Elements['Elements'][x], E0-0.05),xraylib.CS_Photo(Elements['Elements'][x], E0+0.05)]
                Photo_XS = np.vstack((Photo_XS,newPXS)) 

        # Calcualte Mass Weighted Photo Absorption Cross Section:
        mu_tot = []
        for x in range(0,Elements['nElements']):
            if x ==0:
                mu_tot = np.multiply(Photo_XS[x,:],Elements['massFractions'][x])
            else:
                new_mu = np.multiply(Photo_XS[x,:],Elements['massFractions'][x])
                mu_tot = np.vstack((mu_tot, new_mu))

        mu_ave = np.sum(mu_tot, axis = 0)

        # Calculate Sample mass @ E0 + 50 eV and edge step

        mass = AL*Area/mu_ave[1]

        step = np.multiply(np.divide(np.multiply(Elements['massFractions'], mass), Area), np.subtract(Photo_XS[:,1], Photo_XS[:,0]))
        step = np.max(step)

        #return Error_message, E0, mass, step

    else:
        # Determine Photabsorption Cross Sections for element at E0 +/- 50 eV
        Photo_XS = [xraylib.CS_Photo(Elements['Elements'][0], E0-0.05), xraylib.CS_Photo(Elements['Elements'][0], E0+0.05)]
    
        # Calculate Sample mass @ E0 + 50 eV and edge step

        mass = AL*Area/Photo_XS[1]
        step = (mass/Area)*(Photo_XS[1]-Photo_XS[0])
        
    # Clean up the Units, E0 in eV, mass in mg
    E0 = E0*1000
    mass = mass*1000
    
    return E0, mass, step


def XASStoichCalc(Sample1, Sample2, Sample1_DR, Sample2_DR):
    '''
    Calculates the combined chemical formula for a sample and a diluement given
    a ratio of mass components.

    Parameters
    ----------
    Sample1 : STR
        Chemcial formula of the sample. parentheses, even nested, can be used. 
        Numbers of atoms are placed to the left of the atomic symbol (case sensitive)
        with no special characters. E.g. 'H2' or H2O, Na2SO4, or Pt0.5MgO.
    Sample2 : STR
        Chemcial formula of the diluent. parentheses, even nested, can be used. 
        Numbers of atoms are placed to the left of the atomic symbol (case sensitive)
        with no special characters. E.g. 'H2' or H2O, Na2SO4, or Pt0.5MgO.
    Sample1_DR : INT or FLOAT
        Mass of the first sample wiht respect to the second. E.g. if the ratio was
        Sample1:Sample2 = 1:5, Sample1_DR = 1.
    Sample2_DR : INT or FLOAT
        Mass of the second sample wiht respect to the first. E.g. if the ratio was
        Sample1:Sample2 = 1:5, Sample2_DR = 5.


    Returns
    -------
    Error_message : STR
        Error message used to identify problems in the funciton inputs.
    Diluted_Sample_Formula : STR
        Chemical formula of the mixing of two samples givne theri mass dilution ratios
    '''
    Diluted_Sample_Formula = ''
    
    #Extract Chemcial Information from Sample
    Sample1_Elements = xraylib.CompoundParser(Sample1)
    
    #Extract Chemcial Information from Sample
    Sample2_Elements = xraylib.CompoundParser(Sample2)
    
    #Calculate New Nass Fractions
    Updated_MF = []

    for x in range(0,Sample1_Elements['nElements']):
        if x == 0:
            Updated_MF = [Sample1_Elements['Elements'][x], Sample1_Elements['massFractions'][x]*Sample1_DR/(Sample1_DR + Sample2_DR)]
        else:
            new_line = [Sample1_Elements['Elements'][x], Sample1_Elements['massFractions'][x]*Sample1_DR/(Sample1_DR + Sample2_DR)]    
            Updated_MF = np.vstack((Updated_MF,new_line))

    if Sample2_DR > 0:
        for x in range(0,Sample2_Elements['nElements']):
            new_line = [Sample2_Elements['Elements'][x], Sample2_Elements['massFractions'][x]*Sample2_DR/(Sample1_DR + Sample2_DR)]   
            Updated_MF = np.vstack((Updated_MF,new_line)) 

    #Calcualte Moles of each component
    mol = []
    for x in range(0,np.shape(Updated_MF)[0]):
        if x == 0:
            mol = Updated_MF[x,1]/xraylib.AtomicWeight(int(Updated_MF[x,0]))
        else:
            new_mol = Updated_MF[x,1]/xraylib.AtomicWeight(int(Updated_MF[x,0]))
            mol = np.vstack((mol,new_mol))

    mol = mol/min(mol)

    #Build New String
    for x in range(0,np.shape(Updated_MF)[0]):
        if x == 0:
            Sample_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Updated_MF[x,0])), float(mol[x])) 
        else:
            new_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Updated_MF[x,0])), float(mol[x]))
            Sample_String = Sample_String+new_String

    Diluted_Sample = xraylib.CompoundParser(Sample_String)

    #Build Condensed String

    for x in range(0,Diluted_Sample['nElements']):
        if x == 0:
            Diluted_Sample_Formula = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Diluted_Sample['Elements'][x])), float(Diluted_Sample['nAtoms'][x])) 
        else:
            new_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Diluted_Sample['Elements'][x])), float(Diluted_Sample['nAtoms'][x]))
            Diluted_Sample_Formula = Diluted_Sample_Formula+new_String

    return  Diluted_Sample_Formula



def metalCalculateSample(Metal_Site1, Metal1_Loading, Metal_Site2, Metal2_Loading, Support):
    '''
    Calculates the chemical formula of a material consiting of two metal site compositsions,
    weight loadings, and a support.

    Parameters
    ----------
    Metal_Site1 : STR
        Chemcial formula of the metal site on the support. parentheses, even nested, can be used. 
        Numbers of atoms are placed to the left of the atomic symbol (case sensitive)
        with no special characters. E.g. 'H2' or H2O, Na2SO4, or Pt0.5MgO.
    Metal1_Loading : INT or FLOAT
        [%] Weight % loading of first metal site.
    Metal_Site2 : STR
        Chemcial formula of a second metal site on the support. parentheses, even nested, can be used. 
        Numbers of atoms are placed to the left of the atomic symbol (case sensitive)
        with no special characters. E.g. 'H2' or H2O, Na2SO4, or Pt0.5MgO.
    Metal2_Loading : INT or FLOAT
        [%] Weight % loading of first metal site.
    Support : STR
        Chemcial formula of the support. parentheses, even nested, can be used. 
        Numbers of atoms are placed to the left of the atomic symbol (case sensitive)
        with no special characters. E.g. 'H2' or H2O, Na2SO4, or Pt0.5MgO.

    Returns
    -------
    Sample_String : TYPE
        DESCRIPTION.

    '''
          
    # Parse metal Site 1 and Support 
    MetalSite1_Elements = xraylib.CompoundParser(Metal_Site1)
    
    Support_Elements = xraylib.CompoundParser(Support)

   
    #Calculate New Nass Fractions
    Updated_MF = []

    if Metal_Site2 == '':
        #Weight metal site 1 fractions and store them + atomic number
        for x in range(0,MetalSite1_Elements['nElements']):
            if x == 0:
                Updated_MF = [MetalSite1_Elements['Elements'][x], MetalSite1_Elements['massFractions'][x]*Metal1_Loading/100]
            else:
                new_line = [MetalSite1_Elements['Elements'][x], MetalSite1_Elements['massFractions'][x]*Metal1_Loading/100]   
                Updated_MF = np.vstack((Updated_MF,new_line))
                
        #Add Support Mass Fractions
        for x in range(0,Support_Elements['nElements']):
            new_line = [Support_Elements['Elements'][x], Support_Elements['massFractions'][x]*(1-(Metal1_Loading)/100)]   
            Updated_MF = np.vstack((Updated_MF,new_line))
    
    else:
        #Weight metal site 1 fractions and store them + atomic number      
        for x in range(0,MetalSite1_Elements['nElements']):
            if x == 0:
                Updated_MF = [MetalSite1_Elements['Elements'][x], MetalSite1_Elements['massFractions'][x]*Metal1_Loading/100]
            else:
                new_line = [MetalSite1_Elements['Elements'][x], MetalSite1_Elements['massFractions'][x]*Metal1_Loading/100]   
                Updated_MF = np.vstack((Updated_MF,new_line))
    
        #Weight metal site 2 fractions and store them + atomic number      
        MetalSite2_Elements = xraylib.CompoundParser(Metal_Site2)
        Metal2_Loading = float(Metal2_Loading)
        for x in range(0,MetalSite2_Elements['nElements']):
            new_line = [MetalSite2_Elements['Elements'][x], MetalSite2_Elements['massFractions'][x]*Metal2_Loading/100]   
            Updated_MF = np.vstack((Updated_MF,new_line))
            
        #Add Support Mass Fractions
        for x in range(0,Support_Elements['nElements']):
            new_line = [Support_Elements['Elements'][x], Support_Elements['massFractions'][x]*(1-(Metal1_Loading+Metal2_Loading)/100)]   
            Updated_MF = np.vstack((Updated_MF,new_line))

    
    #Calcualte Moles of each component
    mol = []
    for x in range(0,np.shape(Updated_MF)[0]):
        if x == 0:
            mol = Updated_MF[x,1]/xraylib.AtomicWeight(int(Updated_MF[x,0]))
        else:
            new_mol = Updated_MF[x,1]/xraylib.AtomicWeight(int(Updated_MF[x,0]))
            mol = np.vstack((mol,new_mol))
    
    mol = mol/min(mol)

   
    #Build New String
    for x in range(0,np.shape(Updated_MF)[0]):
        if x == 0:
            Sample_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Updated_MF[x,0])), float(mol[x])) 
        else:
            new_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Updated_MF[x,0])), float(mol[x]))
            Sample_String = Sample_String+new_String

    Constructed_Sample = xraylib.CompoundParser(Sample_String)

    
    #Build Condensed String
    for x in range(0,Constructed_Sample['nElements']):
        if x == 0:
            Sample_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Constructed_Sample['Elements'][x])), float(Constructed_Sample['nAtoms'][x])) 
        else:
            new_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Constructed_Sample['Elements'][x])), float(Constructed_Sample['nAtoms'][x]))
            Sample_String = Sample_String+new_String
    
    return Sample_String


def ComplexCalculateSample(Complex, Metal_Loading, Metal_Site, Support):
    '''
    Calculate the stoichiometry of a supported complex catalyst based upon the complex,
    its loading, or the metal center and its loading, and the support

    Parameters
    ----------
    Complex : STR
        Chemcial formula of the metal site on the support. parentheses, even nested, can be used. 
        Numbers of atoms are placed to the left of the atomic symbol (case sensitive)
        with no special characters. E.g. 'H2' or H2O, Na2SO4, or Pt0.5MgO.
    Metal_Loading : INT or FLOAT
        [%] Weight % loading of first metal site.
    Metal_Site : STR
        Element in the complex
    Support : STR
        Chemcial formula of the support. parentheses, even nested, can be used. 
        Numbers of atoms are placed to the left of the atomic symbol (case sensitive)
        with no special characters. E.g. 'H2' or H2O, Na2SO4, or Pt0.5MgO.

    Returns
    -------
    Sample_String : TYPE
        DESCRIPTION.

    '''
               
    # Parse metal Site 1 and Support 
    MetalSite_Elements = xraylib.CompoundParser(Complex)
    
    Support_Elements = xraylib.CompoundParser(Support)

   
    #Calculate New Nass Fractions
    Updated_MF = []
    
    #Find Metal Site in Complex
    ind = MetalSite_Elements['Elements'].index(xraylib.SymbolToAtomicNumber(Metal_Site))
    wt_Factor = Metal_Loading/MetalSite_Elements['massFractions'][ind]
    
    #Weight metal site 1 fractions and store them + atomic number      
    for x in range(0,MetalSite_Elements['nElements']):
        if x == 0:
            Updated_MF = [MetalSite_Elements['Elements'][x], MetalSite_Elements['massFractions'][x]*wt_Factor/100]
        else:
            new_line = [MetalSite_Elements['Elements'][x], MetalSite_Elements['massFractions'][x]*wt_Factor/100]   
            Updated_MF = np.vstack((Updated_MF,new_line))
    
    complex_MF = np.sum(Updated_MF[:,1])
    
    #Add Support Mass Fractions
    for x in range(0,Support_Elements['nElements']):
        new_line = [Support_Elements['Elements'][x], Support_Elements['massFractions'][x]*(1-complex_MF)]   
        Updated_MF = np.vstack((Updated_MF,new_line))

    
    #Calcualte Moles of each component
    mol = []
    for x in range(0,np.shape(Updated_MF)[0]):
        if x == 0:
            mol = Updated_MF[x,1]/xraylib.AtomicWeight(int(Updated_MF[x,0]))
        else:
            new_mol = Updated_MF[x,1]/xraylib.AtomicWeight(int(Updated_MF[x,0]))
            mol = np.vstack((mol,new_mol))
    
    mol = mol/min(mol)

   
    #Build New String
    for x in range(0,np.shape(Updated_MF)[0]):
        if x == 0:
            Sample_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Updated_MF[x,0])), float(mol[x])) 
        else:
            new_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Updated_MF[x,0])), float(mol[x]))
            Sample_String = Sample_String+new_String

    Constructed_Sample = xraylib.CompoundParser(Sample_String)

    
    #Build Condensed String
    for x in range(0,Constructed_Sample['nElements']):
        if x == 0:
            Sample_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Constructed_Sample['Elements'][x])), float(Constructed_Sample['nAtoms'][x])) 
        else:
            new_String = '{0:s}{1:0.6f}'.format(xraylib.AtomicNumberToSymbol(int(Constructed_Sample['Elements'][x])), float(Constructed_Sample['nAtoms'][x]))
            Sample_String = Sample_String+new_String
    
    return Sample_String
    
