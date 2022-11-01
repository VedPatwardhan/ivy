import ivy
from ivy.func_wrapper import with_unsupported_dtypes
from ivy.functional.frontends.torch.func_wrapper import to_ivy_arrays_and_back


@to_ivy_arrays_and_back
def flip(input, dims):
    return ivy.flip(input, axis=dims)


@to_ivy_arrays_and_back
def fliplr(input):
    ivy.assertions.check_greater(
        len(input.shape),
        2,
        allow_equal=True,
        message="requires tensor to be at least 2D",
    )
    return ivy.flip(input, axis=(-1,))


@to_ivy_arrays_and_back
def roll(input, shifts, dims=None):
    return ivy.roll(input, shifts, axis=dims)


@to_ivy_arrays_and_back
@with_unsupported_dtypes(
    {"1.11.0 and below": ("uint8", "bfloat16", "float16"), "1.12.1": ()},
    "torch",
)
def cumsum(input, dim, *, dtype=None, out=None):
    return ivy.cumsum(input, axis=dim, dtype=dtype, out=out)


@to_ivy_arrays_and_back
@with_unsupported_dtypes({"1.11.0 and below": ("float16", "bfloat16")}, "torch")
def trace(input):
    if "int" in input.dtype:
        input = input.astype("int64")
    target_type = "int64" if "int" in input.dtype else input.dtype
    return ivy.astype(ivy.trace(input), target_type)


@to_ivy_arrays_and_back
def tril_indices(row, col, offset=0, *, dtype="int64", device="cpu", layout=None):
    sample_matrix = ivy.tril(ivy.ones((row, col), device=device), k=offset)
    return ivy.stack(ivy.nonzero(sample_matrix)).astype(dtype)


@to_ivy_arrays_and_back
def cumprod(input, dim, *, dtype=None, out=None):
    return ivy.cumprod(input, axis=dim, dtype=dtype, out=out)


@to_ivy_arrays_and_back
def diagonal(input, offset=0, dim1=0, dim2=1):
    return ivy.diagonal(input, offset=offset, axis1=dim1, axis2=dim2)


@to_ivy_arrays_and_back
def cartesian_prod(*tensors):
    if len(tensors) == 1:
        return tensors

    ret = ivy.meshgrid(*tensors, indexing="ij")
    ret = ivy.stack(ret, axis=-1)
    ret = ivy.reshape(ret, shape=(-1, len(tensors)))

    return ret


@to_ivy_arrays_and_back
def triu_indices(row, col, offset=0, dtype="int64", device="cpu", layout=None):
    # TODO: Handle layout flag when possible.
    sample_matrix = ivy.triu(ivy.ones((row, col), device=device), k=offset)
    return ivy.stack(ivy.nonzero(sample_matrix)).astype(dtype)


@to_ivy_arrays_and_back
def triu(input, diagonal=0, *, out=None):
    return ivy.triu(input, k=diagonal, out=out)


@to_ivy_arrays_and_back
def tril(input, diagonal=0, *, out=None):
    return ivy.tril(input, k=diagonal, out=out)


@to_ivy_arrays_and_back
def flatten(input, start_dim=0, end_dim=-1):
    return ivy.flatten(input, start_dim=start_dim, end_dim=end_dim)


@to_ivy_arrays_and_back
def renorm(input, p, dim, maxnorm, *, out=None):
    # Torch hardcodes this magic number
    epsilon = 1e-07

    # Torch performs a conversion here for numerical stability
    # But we wish to return an output with the same dtype as the input.
    original_dtype = input.dtype
    input = ivy.astype(input, ivy.float64)

    # To iterate through the n-th dimension of `input`, it is easiest to swap
    # the dimension that we wish to iterate through to be first, then iterate
    # through the re-ordered data. This re-ordering is fine for our purposes
    # as we calculate the p-norms and they are all order agnostic. That is,
    # we may re-order the elements of any vector, and as long as none are
    # added, edited, or removed, the p-norm will be the same.
    input_swapped = ivy.swapaxes(input, 0, dim)
    individual_tensors = [input_swapped[i, ...] for i in range(input_swapped.shape[0])]
    ret = []
    for individual_tensor in individual_tensors:
        # These tensors may be multidimensional, but must be treated as a single vector.
        original_shape = individual_tensor.shape
        tensor_flattened = flatten(individual_tensor)

        # Don't scale up to the maximum norm, only scale down to it.
        norm = ivy.vector_norm(tensor_flattened, axis=0, ord=p)
        multiplier = ivy.minimum(maxnorm / (norm + epsilon), ivy.ones_like(norm))

        # Store the result in its original shape
        ret.append(
            ivy.reshape(ivy.multiply(tensor_flattened, multiplier), original_shape)
        )

    # We must undo our axis swap from the start.
    ret = ivy.asarray(ret, dtype=original_dtype)
    ret = ivy.swapaxes(ret, 0, dim)
    ret = ivy.reshape(ret, input.shape)

    if ivy.exists(out):
        ivy.inplace_update(out, ret)
    return ret


@to_ivy_arrays_and_back
def logcumsumexp(input, dim, *, out=None):
    if len(input.shape) == 0:
        ret = input
    else:
        # For numerical stability, cast to float64
        # We cast back to the original type at the end.
        original_dtype = input.dtype
        exp_input = ivy.exp(input.astype("float64"))
        summed_exp_input = ivy.cumsum(exp_input, axis=dim)
        ret = ivy.log(summed_exp_input).astype(original_dtype)
    if ivy.exists(out):
        ivy.inplace_update(out, ret)
    return ret


@to_ivy_arrays_and_back
def repeat_interleave(input, repeats, dim=None, *, output_size=None):
    return ivy.repeat(input, repeats, axis=dim)


@to_ivy_arrays_and_back
def ravel(input):
    return ivy.reshape(input, (-1,))


@to_ivy_arrays_and_back
def rot90(input, k, dims):
    total_dims = ivy.get_num_dims(input)
    total_rot_dims = len(dims)

    ivy.assertions.check_greater(
        total_dims,
        2,
        allow_equal=True,
        message="expected total dims >= 2, but got total dims = " + str(total_dims),
    )

    ivy.assertions.check_equal(
        total_rot_dims,
        2,
        message="expected total rotation dims == 2, but got dims = "
        + str(total_rot_dims),
    )

    ivy.assertions.check_equal(
        dims[0],
        dims[1],
        inverse=True,
        message="expected rotation dims to be different, but got dim0 = "
        + str(dims[0])
        + " and dim1 = "
        + str(dims[1]),
    )

    ivy.assertions.check_equal(
        ivy.abs(dims[0] - dims[1]),
        total_dims,
        inverse=True,
        message="expected rotation dims to be different, but got dim0 = "
        + str(dims[0])
        + " and dim1 = "
        + str(dims[1]),
    )

    # range of dims
    ivy.assertions.check_less(
        dims[0],
        total_dims,
        message="Rotation dim0 out of range, dim0 = " + str(dims[0]),
    )

    ivy.assertions.check_greater(
        dims[0],
        -total_dims,
        allow_equal=True,
        message="Rotation dim0 out of range, dim0 = " + str(dims[0]),
    )

    ivy.assertions.check_less(
        dims[1],
        total_dims,
        message="Rotation dim1 out of range, dim1 = " + str(dims[1]),
    )

    ivy.assertions.check_greater(
        dims[1],
        -total_dims,
        allow_equal=True,
        message="Rotation dim1 out of range, dim1 = " + str(dims[1]),
    )

    k = (4 + (k % 4)) % 4
    new_axes = list(range(total_dims))
    new_axes[min(dims)], new_axes[max(dims)] = max(dims), min(dims)
    if k == 1:
        flipped = ivy.flip(input, axis=dims[1])
        return ivy.permute_dims(flipped, axes=new_axes, out=flipped)
    elif k == 2:
        return ivy.flip(input, axis=dims)
    elif k == 3:
        flipped = ivy.flip(input, axis=dims[0])
        return ivy.permute_dims(flipped, axes=new_axes, out=flipped)
    else:
        return ivy.copy_array(input)


@to_ivy_arrays_and_back
def vander(x, N=None, increasing=False):
    if N == 0:
        return ivy.array([], dtype=x.dtype)
    else:
        return ivy.vander(x, N=N, increasing=increasing, out=None)


@to_ivy_arrays_and_back
@with_unsupported_dtypes({"1.11.0 and below": ("int8",)}, "torch")
def lcm(input, other, *, out=None):
    return ivy.lcm(input, other, out=out)


@to_ivy_arrays_and_back
def einsum(equation, *operands):
    return ivy.einsum(equation, *operands)


def _valid_shapes(input, weight, bias, stride, padding, groups, transpose=False):

    in_channels = input.shape[1]
    out_channels = weight.shape[0] if not transpose else weight.shape[1] * groups

    ivy.assertions.check_equal(
        in_channels % groups, 0, message="in_channels must be divisible by groups"
    )
    ivy.assertions.check_equal(
        out_channels % groups, 0, message="out_channels must be divisible by groups"
    )

    if bias is not None:
        ivy.assertions.check_equal(
            bias.shape[0],
            out_channels,
            message="bias must be same shape as out_channels",
        )

    if padding == "same":
        if isinstance(stride, int):
            ivy.assertions.check_equal(
                stride, 1, message="padding cannot be 'same' for stride > 1"
            )
        else:
            for i in padding:
                ivy.assertions.check_equal(
                    i, 1, message="padding cannot be 'same' for stride > 1"
                )

    if not transpose:
        in_channels_by_groups = weight.shape[1]
        ivy.assertions.check_equal(
            in_channels,
            in_channels_by_groups * groups,
            message="in_channels must be consistent",
        )
    else:
        ivy.assertions.check_equal(
            in_channels, weight.shape[0], message="out_channels must be consistent"
        )


@to_ivy_arrays_and_back
def conv1d(input, weight, bias=None, stride=1, padding=0, dilation=1, groups=1):
    _valid_shapes(input, weight, bias, stride, padding, groups)

    if type(padding) == str:
        padding = padding.upper()
    else:
        _pad_w = padding if isinstance(padding, int) else padding[0]
        input = ivy.zero_pad(
            input,
            pad_width=[(0, 0), (0, 0), (_pad_w, _pad_w)],
        )
        padding = "VALID"

    weight = ivy.permute_dims(weight, axes=(2, 1, 0))

    ret = ivy.conv(
        input,
        weight,
        stride,
        padding,
        data_format="channel_first",
        dilations=dilation,
        feature_group_count=groups,
        dims=1,
    )

    if bias is not None:
        return ivy.add(ret, ivy.expand_dims(bias, axis=(0, 2)))
    return ret


@to_ivy_arrays_and_back
def conv2d(input, weight, bias=None, stride=1, padding=0, dilation=1, groups=1):
    _valid_shapes(input, weight, bias, stride, padding, groups)

    if isinstance(padding, str):
        padding = padding.upper()
    else:
        _pad_h, _pad_w = (
            (padding, padding) if isinstance(padding, int) else (padding[0], padding[1])
        )
        input = ivy.zero_pad(
            input, pad_width=[(0, 0), (0, 0), (_pad_h, _pad_h), (_pad_w, _pad_w)]
        )
        padding = "VALID"

    weight = ivy.permute_dims(weight, axes=(2, 3, 1, 0))
    ret = ivy.conv(
        input,
        weight,
        stride,
        padding,
        data_format="channel_first",
        dilations=dilation,
        feature_group_count=groups,
    )
    if bias is not None:
        return ivy.add(ret, ivy.expand_dims(bias, axis=(0, 2, 3)))
    return ret


@to_ivy_arrays_and_back
def conv3d(input, weight, bias=None, stride=1, padding=0, dilation=1, groups=1):
    _valid_shapes(input, weight, bias, stride, padding, groups)

    if isinstance(padding, str):
        padding = padding.upper()
    else:
        _pad_t, _pad_h, _pad_w = (
            (padding, padding, padding)
            if isinstance(padding, int)
            else (padding[0], padding[1], padding[2])
        )
        input = ivy.zero_pad(
            input,
            pad_width=[
                (0, 0),
                (0, 0),
                (_pad_t, _pad_t),
                (_pad_h, _pad_h),
                (_pad_w, _pad_w),
            ],
        )
        padding = "VALID"

    weight = ivy.permute_dims(weight, axes=(2, 3, 4, 1, 0))
    ret = ivy.conv(
        input,
        weight,
        stride,
        padding,
        data_format="channel_first",
        dilations=dilation,
        feature_group_count=groups,
        dims=3,
    )
    if bias is not None:
        return ivy.add(ret, ivy.expand_dims(bias, axis=(0, 2, 3, 4)))
    return ret


@to_ivy_arrays_and_back
def cross(input, other, dim=None, *, out=None):
    if dim is None:
        dim = -1
    input, other = ivy.promote_types_of_inputs(input, other)

    if dim is not None:
        return ivy.cross(input, other, axisa=-1, axisb=-1, axisc=-1, axis=dim, out=out)
