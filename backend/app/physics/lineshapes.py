from abc import ABC,abstractmethod
import numpy as np
class LineShape(ABC):
 @abstractmethod
 def evaluate(self,s:np.ndarray)->np.ndarray: ...
class RelativisticBreitWigner(LineShape):
 def __init__(self,mass:float,width:float): self.mass,self.width=mass,width
 def evaluate(self,s): return 1.0/(self.mass**2-s-1j*self.mass*self.width)
