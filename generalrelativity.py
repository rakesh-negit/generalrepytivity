import sympy
import itertools

def get_all_multiindices(p, n):
    '''
    This function returns a list of all the tuples of the form (a_1, ..., a_p)
    with a_i between 1 and n-1. These tuples serve as multiindices for tensors.
    '''
    if p == 0:
        return [None]
    if p == 1:
        return [(k, ) for k in range(n)]
    if p > 1:
        return list(itertools.product(range(n), repeat=p))

def is_multiindex(multiindex, n, c_dimension):
    '''
    This function determines if a tuple (or None object) is a multiindex or not
    according to these rules:
    1. None is a multiindex of length 0 (i.e. if the covariant or contravariant dimension
    is 0, None is the only multiindex)
    2. The length of a multiindex must be equal to the c_dimension
    3. Each value in the multiindex varies between 0 and n-1.
    '''
    if multiindex == None:
        if c_dimension == 0:
            return True
        else:
            return False
    if len(multiindex) != c_dimension:
        return False
    for value in multiindex:
        if value < 0 or value >= n:
            return False
    
    return True


class Tensor:
    '''
    This class represents a tensor object in a given basis.

    To construct a (p,q)-Tensor, one must pass two arguments:
    1. _type: a pair of values p (the contravariant dimension) and q (the covariant dimension).
    2. the non-zero values, which is a dict whose value are pairs of the form (a, b)
    where a and b are multi-indices such that $\Gamma^a_b = value$, the values that
    don't appear in this dict are assumed to be 0.

    To-Do:
        - Fix the standard and start writing the .tex.
    '''
    def __init__(self, basis, _type, dict_of_values):
        self.basis = basis
        self.covariant_dim = _type[0]
        self.contravariant_dim = _type[1]
        self.type = _type

        for key in dict_of_values:
            a, b = key
            if not is_multiindex(a, len(self.basis), self.contravariant_dim):
                raise ValueError('The multiindex {} is inconsistent with dimension {}'.format(a, self.contravariant_dim))
            if not is_multiindex(b, len(self.basis), self.covariant_dim):
                raise ValueError('The multiindex {} is inconsistent with dimensions {}'.format(b, self.covariant_dim))

        self.dict_of_values = dict_of_values
    
    def __eq__(self, other):
        if self.basis == other.basis:
            if self.type == other.type:
                if self.get_all_values() == other.get_all_values():
                    return True
        return False

    
    def __getitem__(self, pair):
        a, b = pair
        if isinstance(a, int):
            if isinstance(b, int):
                if (is_multiindex((a, ), len(self.basis), self.contravariant_dim) and
                    is_multiindex((b, ), len(self.basis), self.covariant_dim)):
                    if ((a, ), (b, )) in self.dict_of_values:
                        return self.dict_of_values[((a, ), (b, ))]
                    else:
                        return 0
                else:
                    raise KeyError('There\'s a problem with the multiindices ({}, ) and ({}, )'.format(a, b))
            if is_multiindex(b, len(self.basis), self.covariant_dim):
                if ((a, ), b) in self.dict_of_values:
                    return self.dict_of_values[((a, ), b)]
                else:
                    return 0
        if is_multiindex(a, len(self.basis), self.contravariant_dim):
            if isinstance(b, int):
                if (a, (b, )) in self.dict_of_values:
                    return self.dict_of_values[(a, (b, ))]
                else:
                    return 0
            if is_multiindex(b, len(self.basis), self.covariant_dim):
                if (a, b) in self.dict_of_values:
                    return self.dict_of_values[(a, b)]
                else:
                    return 0
        raise KeyError('There\'s something wrong with the pair of multiindices {} and {}'.format(a, b))

    def __repr__(self):
        string = ''
        for key in self.dict_of_values:
            string += '({})'.format(self.dict_of_values[key])
            a, b = key
            if a != None:
                substring_of_a = ''
                for ind in a:
                    substring_of_a += '{}* \\otimes '.format(self.basis[ind])
                substring_of_a = substring_of_a[:-len(' \\otimes ')]
                string += substring_of_a
            if b != None:
                if a != None:
                    string += ' \\otimes '
                for ind in b:
                    string += '{} \\otimes '.format(self.basis[ind])
                string = string[:-len(' \\otimes ')]
            string += ' + '
        string = string[:-3]
        return string

    def __add__(self, other):
        if not isinstance(other, Tensor):
            raise ValueError('Cannot add a tensor with a {}'.format(type(other)))
        
        if other.basis != self.basis or other.type != self.type:
            raise ValueError('Tensors should be of the same type and have the same basis.')

        result_dict = self.dict_of_values.copy()
        for key in other.dict_of_values:
            if key in result_dict:
                result_dict[key] = result_dict[key] + other.dict_of_values[key]
            if key not in result_dict:
                result_dict[key] = other.dict_of_values[key]
        
        result_basis = self.basis
        result_type = self.type
        return Tensor(result_basis, result_type, result_dict)

    def subs(self, list_of_substitutions):
        for value in self.dict_of_values.items:
            value.subs(list_of_substitutions)

    def get_all_values(self):
        new_dict = {}
        dim = len(self.basis)
        covariant_multiindices = get_all_multiindices(self.covariant_dim, dim)
        contravariant_multiindices = get_all_multiindices(self.contravariant_dim, dim)
        for a in contravariant_multiindices:
            for b in covariant_multiindices:
                if (a,b) in self.dict_of_values:
                    new_dict[a, b] = self.dict_of_values[a, b]
                else:
                    new_dict[a, b] = 0
        return new_dict

def tensor_from_matrix(matrix, basis):
    '''
    This function takes a square matrix and a basis and retruns a (0,2)-tensor in that basis.
    '''
    dict_of_values = {}
    for i in range(len(matrix.tolist())):
        for j in range(len(matrix.tolist())):
            dict_of_values[(i,j), None] = matrix[i, j]
    return Tensor(basis, (0, 2), dict_of_values)

class Metric:
    def __init__(self, _matrix, basis):
        self.matrix = _matrix
        self.basis = basis
        self.as_tensor = tensor_from_matrix(self.matrix, self.basis)

def contract_indices(tensor, i, j):
    '''
    Returns the resulting tensor of formally contracting the indices i and j 
    of the given tensor.
    '''
    dim = len(tensor.basis)
    covariant_dim = tensor.covariant_dim
    contravariant_dim = tensor.contravariant_dim
    if covariant_dim < 1 or contravariant_dim < 1:
        raise ValueError('One of the dimensions in the type {} is less than one.'.format(tensor.type))
    if i < 0 or i >= contravariant_dim:
        raise ValueError('{} is either negative or bigger than the contravariant dimension minus one {}'.format(i,
                                                                                    contravariant_dim-1))
    if j < 0 or j >= covariant_dim:
        raise ValueError('{} is either negative or bigger than the covariant dimension minus one {}'.format(j,
                                                                                    covariant_dim-1))

    covariant_indices = get_all_multiindices(covariant_dim-1, dim)
    contravariant_indices = get_all_multiindices(contravariant_dim-1, dim)
    print(covariant_indices)
    print(contravariant_indices)
    new_tensor_dict = {}
    for a in contravariant_indices:
        for b in covariant_indices:
            sumand = 0
            for r in range(dim):
                a_extended = a[:i] + (r, ) + a[i:]
                b_extended = b[:j] + (r, ) + b[j:]
                sumand += tensor[a_extended, b_extended]
            new_tensor_dict[a, b] = sumand

    return Tensor(tensor.basis, (contravariant_dim - 1, covariant_dim - 1), new_tensor_dict)

def lower_index(tensor, metric):
    pass