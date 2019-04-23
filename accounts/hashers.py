from django.contrib.auth.hashers import (PBKDF2PasswordHasher,
                    BCryptSHA256PasswordHasher)

class PBKDF2WrappedBCryptSHA256PasswordHasher(BCryptSHA256PasswordHasher):
    aligorithm ='pbkdf2_wrapped_bcrypt'
    
    def encode_bcrypt_sha256(self,bcrypt,salt, iterations=None):
        return super().encode(bcrypt,salt,iterations)

    def encode(self, password,salt,iterations=None):
        _,_,bcrypt =BCryptSHA256PasswordHasher().encode(password, salt).split('$',2)
        return self.encode_bcrypt_sha256(bcrypt,salt,iterations)
