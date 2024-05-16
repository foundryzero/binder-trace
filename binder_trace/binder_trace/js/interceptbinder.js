const BINDER_WRITER_READ = 0xc0306201;
const BC_TRANSACTION = 0x40406300;
const BC_REPLY = 0x40406301;

var parameters = {};

// Note: this filtering mechanism here doesn't actually get used - I moved to filtering displayed parcels rather than
// filtering which parcels are captured.
var exclude_re = { test(i) { return false } };
var exclude_list = Array();

// Special case: if there are no exclusions and any inclusions, this is set to true
// to exclude everything by default instead of including everything.
var just_include = false;

var include_re = { test(i) { return false } };
var include_list = Array();

var verbosity = 1;

var silent = true;

var android_version = 11; // Default to android 11, but a different version can be provided through the options object.

rpc.exports = {
    init: function (stage, param) {
        parameters = param;

        if (!('exclude' in parameters || 'exclude_re' in parameters) && ('include' in parameters || 'include_re' in parameters)) {
            just_include = true;
        }

        if ('exclude' in parameters) {
            exclude_list = parameters.exclude
        }

        if ('exclude_re' in parameters) {
            try {
                exclude_re = new RegExp(parameters.exclude_re)
            } catch (e) {
                console.error("Invalid exclusion regex")
            }
        }

        if ('include' in parameters) {
            just_include = true
            include_list = parameters.include
        }

        if ('include_re' in parameters) {
            try {
                include_re = new RegExp(parameters.include_re)
            } catch (e) {
                console.error("Invalid inclusion regex")
            }
        }

        if ('verbosity' in parameters) {
            switch (parameters.verbosity) {
                case 0:
                    verbosity = 0;
                    break;
                case 1:
                    verbosity = 1;
                    break;
                case 2:
                    verbosity = 2;
                    break;

                default:
                    console.error("Invalid verbosity value")
            }
        }

        if ('connected' in parameters) {
            silent = true;
        }

        if ('version' in parameters) {
            android_version = parameters.version
        }


    }
}

function check_printable_descriptor(descriptor) {
    var included = !just_include; // Usually set to true, false if there are only inclusion conditions. 

    //console.log(include_list)

    if (exclude_list.includes(descriptor) || exclude_re.test(descriptor)) {
        included = false;
    }

    if (include_list.includes(descriptor) || include_re.test(descriptor)) {
        included = true;
    }

    return included
}

function binder_write_read(ptr) {
    return {
        ptr: ptr,
        get write_size() { return this.ptr.readU64(); },
        get write_consumed() { return this.ptr.add(8).readU64(); },
        get write_buffer() { return this.ptr.add(16).readPointer(); },
        get read_size() { return this.ptr.add(24).readU64(); },
        get read_consumed() { return this.ptr.add(32).readU64(); },
        get read_buffer() { return this.ptr.add(40).readPointer(); }
    }
}

function interface_token(ptr) {
    return {
        ptr: ptr,
        get strict_mode_policy() { return this.ptr.readU32(); },
        get work_source_uid() { return this.ptr.add(4).readU32(); },
        get version_header() { return this.ptr.add(8).readU32(); },
        get descriptor_length() {
            if (android_version >= 10) {
                return this.ptr.add(12).readU32();
            } else {
                return this.ptr.add(4).readU32();
            }
        },
        get descriptor() {
            if (android_version >= 10) {
                return this.ptr.add(16).readUtf16String(this.descriptor_length);
            } else {
                return this.ptr.add(8).readUtf16String(this.descriptor_length);
            }
        },
    }
}

function parcel(ptr) {
    if (Process.arch == "ia32" || Process.arch == "arm") {
        // Return 32-bit parcel
        return {
            ptr: ptr,
            get error() { return this.ptr.readU32() },
            get data() { return this.ptr.add(4).readPointer() },
            get data_size() { return this.ptr.add(8).readU32() },
            get data_capacity() { return this.ptr.add(12).readU32() },
            get data_pos() { return this.ptr.add(16).readU32() },
            get objects() { return this.ptr.add(20).readPointer() },
            get objects_size() { return this.ptr.add(24).readU32() },
            get objects_capacity() { return this.ptr.add(28).readU32() },
            get next_object_hint() { return this.ptr.add(32).readU32() },
            get objects_sorted() { return this.ptr.add(36).readU8() } // TODO finish parsing this
        }
    } else {
        // Return 64-bit parcel
        return {
            ptr: ptr,
            get error() { return this.ptr.readU64() },
            get data() { return this.ptr.add(8).readPointer() },
            get data_size() { return this.ptr.add(16).readU64() },
            get data_capacity() { return this.ptr.add(24).readU64() },
            get data_pos() { return this.ptr.add(32).readU64() },
            get objects() { return this.ptr.add(40).readPointer() },
            get objects_size() { return this.ptr.add(48).readU64() },
            get objects_capacity() { return this.ptr.add(56).readU64() },
            get next_object_hint() { return this.ptr.add(64).readU64() },
            get objects_sorted() { return this.ptr.add(72).readU8() } // TODO finish parsing this
        }
    }
}

function print_transaction(p, code) {

    var token = interface_token(p.data)

    if(silent) {
        send({"type" : "TRANSACT", "code": code.toInt32()}, p.data.readByteArray(p.data_size))
    } else {

        if (verbosity == 0) {
            console.log(token.descriptor + ":" + code)
        } else if (verbosity == 1) {
            console.log(JSON.stringify({ "name": token.descriptor, "code": code }));
            console.log(hexdump(p.data, {
                length: p.data_size,
                header: true,
                ansi: true
            }));
        } else if (verbosity == 2) {
            console.log('\n\n\n')
            console.log(JSON.stringify({ "name": token.descriptor, "code": code }));
            console.log(hexdump(p.data, {
                length: p.data_size,
                header: true,
                ansi: true
            }));
        }
    }

}

var temp = ptr(0)

// IPCThreadState::transact()
Interceptor.attach(Module.getExportByName("libbinder.so", "_ZN7android14IPCThreadState8transactEijRKNS_6ParcelEPS1_j"), {
    reply: ptr("0x0"),
    descriptor: "",
    code: 0,

    onEnter: function (args) {
        if (!silent) {
            console.log("\n\n\nTRANSACTION " + args[0] + ", " + args[1] + ", " + args[2] + ", " + args[3] + ", " + args[4] + ", " + args[5]);
        }

        var data = parcel(args[3])

        if (data.data.isNull()) {
            //console.log(">> weird packet")
            this.reply = ptr("0x0");
            return;
        }

        if (check_printable_descriptor(interface_token(data.data).descriptor)) {
            print_transaction(data, args[2]);
            if (args[5].toInt32() & 0x1 || args[4].isNull()) {
                //console.log(">> one way packet")
                this.reply = ptr("0x0");
            } else {
                this.reply = parcel(args[4])
                this.code = args[2].toInt32()
                this.descriptor = interface_token(data.data).descriptor
            }
        }
    },

    onLeave: function (retval) {
        if ("data" in this.reply) { // If this.reply is a Parcel
            if (!silent) {
                console.log("REPLY " + this.reply.ptr)
                console.log(hexdump(this.reply.data, { ansi: true, length: this.reply.data_size }));
            } else {
                send({"type": "REPLY", "code": this.code, "descriptor": this.descriptor}, this.reply.data.readByteArray(this.reply.data_size))
            }

            this.reply = ptr(0);

        }
    }
})